import logging
from pathlib import Path
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.loader import async_get_integration

from .card_loader import async_register_cards
from .command import CommandTracker
from .coordinator import DEFAULT_SCAN_INTERVAL, DatakomCoordinator

DOMAIN = "ha_datakom"
_LOGGER = logging.getLogger(__name__)

__all__ = ["DOMAIN", "FUEL_DEFAULTS", "FUEL_RATE_SOURCES", "USER_OUTPUTS", "USER_OUTPUT_SIGNAL", "parse_user_outputs", "_cleanup_old_entities"]

PLATFORMS = ["sensor", "binary_sensor", "button", "switch"]

# Користувацькі виходи контролера (User outputs): номери 1..16
USER_OUTPUTS = 16
# Сигнал «вихід N перемкнуто» (сервіс set_user_output -> перемикач цього виходу)
USER_OUTPUT_SIGNAL = f"{DOMAIN}_user_output"


def parse_user_outputs(value) -> list[int]:
    """«1, 3,5» або [1, 3, 5] -> [1, 3, 5]; ValueError, якщо номер не 1..16."""
    if not value:
        return []
    items = value if isinstance(value, (list, tuple)) else str(value).replace(";", ",").split(",")
    outputs = sorted({int(str(x).strip()) for x in items if str(x).strip()})
    if any(not 1 <= n <= USER_OUTPUTS for n in outputs):
        raise ValueError(f"user outputs must be 1..{USER_OUTPUTS}")
    return outputs

# Источник расхода топлива: auto - датчик (витратомір/ECU), если показывает > 0, иначе модель;
# model - только модель; flowmeter / ecu - только фактический расход с датчика
FUEL_RATE_SOURCES = ["auto", "model", "flowmeter", "ecu"]

# Эмпирическая модель расхода топлива: Q = max(idle_rate, slope * P - offset), л/ч (P - полная мощность, кВА).
# По умолчанию - подгонка по баку реального генератора (запуски 03-08.11.2026): 3.85 л/ч за работу
# + 0.228 л на кВт·ч (≈ 0.217 л на кВА·ч при cos φ ≈ 0.95), т.е. Q = 3.85 + 0.217 * P (offset отрицательный).
# reserve - неиспользуемый остаток топлива (л), не учитывается в расчёте времени работы
FUEL_DEFAULTS = {
    "fuel_idle_rate": 3.85,
    "fuel_slope": 0.217,
    "fuel_offset": -3.85,
    "fuel_reserve": 30,
}
# Прежние значения по умолчанию (до 2.12.0): завышали расход при большой нагрузке на ~40 % и занижали на малой.
# Записи с ровно этими значениями (их не меняли вручную) переводятся на новые при запуске.
FUEL_OLD_DEFAULTS = {"fuel_idle_rate": 2.5, "fuel_slope": 1.014, "fuel_offset": 17.97}

# Карточки Lovelace поставляются с интеграцией: файлы из frontend/ отдаются по этому адресу (там же картинки),
# а сами карточки копируются в www/ha_datakom и подключаются ресурсом панелей автоматически (см. card_loader)
FRONTEND_URL = "/ha_datakom"
FRONTEND_SCRIPTS = ["datakom-controller-card.js", "datakom-controller-card-editor.js"]


async def _async_register_frontend(hass: HomeAssistant) -> None:
    if hass.data.get(f"{DOMAIN}_frontend"):
        return
    hass.data[f"{DOMAIN}_frontend"] = True

    path = str(Path(__file__).parent / "frontend")
    try:
        from homeassistant.components.http import StaticPathConfig
        await hass.http.async_register_static_paths([StaticPathConfig(FRONTEND_URL, path, True)])
    except ImportError:
        # Home Assistant до 2024.7
        hass.http.register_static_path(FRONTEND_URL, path, True)

    # Версия в адресе - чтобы после обновления браузер не брал старый файл из кэша
    version = (await async_get_integration(hass, DOMAIN)).version
    await async_register_cards(hass, DOMAIN, Path(path), FRONTEND_SCRIPTS, FRONTEND_URL, str(version))


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if all(float(entry.data.get(k, -1)) == v for k, v in FUEL_OLD_DEFAULTS.items()):
        hass.config_entries.async_update_entry(entry, data={**entry.data, **{k: FUEL_DEFAULTS[k] for k in FUEL_OLD_DEFAULTS}})
        _LOGGER.info("Datakom: fuel model coefficients updated to the new defaults (3.85 + 0.217 × kVA)")
    """Set up Datakom from a config entry (UI)."""
    await _async_register_frontend(hass)

    coordinator = DatakomCoordinator(
        hass,
        api_url=entry.data.get("api_url", ""),
        language=entry.data.get("language", "uk"),
        scan_interval=int(entry.data.get("scan_interval", DEFAULT_SCAN_INTERVAL)),
    )
    # Без связи с API при старте интеграция всё равно загружается - сущности восстановят последние значения
    await coordinator.async_refresh()
    
    hass.data.setdefault(DOMAIN, {})
    # Хід останньої команди керування (кнопки): після кожного оновлення даних перевіряємо, чи змінився режим
    tracker = CommandTracker(hass)
    entry.async_on_unload(coordinator.async_add_listener(lambda: tracker.check(coordinator.data)))
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator, "data": entry.data, "command": tracker}
    
    # Удаляем старые entity перед созданием новых
    await _cleanup_old_entities(hass, entry)
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _async_register_services(hass)

    return True


SET_USER_OUTPUT_SCHEMA = vol.Schema({
    vol.Required("output"): vol.All(vol.Coerce(int), vol.Range(min=1, max=USER_OUTPUTS)),
    vol.Required("state"): vol.In(["on", "off"]),
})


def _async_register_services(hass: HomeAssistant) -> None:
    """ha_datakom.set_user_output: увімкнути / вимкнути будь-який користувацький вихід 1..16."""
    if hass.services.has_service(DOMAIN, "set_user_output"):
        return

    async def _set_user_output(call: ServiceCall) -> None:
        from .control_api import async_send_control

        runtime = next((r for r in hass.data.get(DOMAIN, {}).values()
                        if isinstance(r, dict) and r.get("data", {}).get("control_key")), None)
        if not runtime:
            raise HomeAssistantError("Datakom: керування вимкнене - не задано ключ керування")
        number, state = call.data["output"], call.data["state"]
        await async_send_control(
            hass, runtime["data"].get("api_url", ""), runtime["data"]["control_key"],
            {"action": "output", "output": number, "state": state},
            runtime["coordinator"], runtime.get("command"), label=f"output {number} {state}",
        )
        # Перемикач цього виходу (якщо показаний) - теж у новий стан
        async_dispatcher_send(hass, USER_OUTPUT_SIGNAL, number, state == "on")

    hass.services.async_register(DOMAIN, "set_user_output", _set_user_output, schema=SET_USER_OUTPUT_SCHEMA)

async def _cleanup_old_entities(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Удаляет старые entity которых больше нет в текущей конфигурации."""
    try:
        entity_registry = er.async_get(hass)
        current_param_ids = [int(pid) if isinstance(pid, str) else pid for pid in entry.data.get("param_ids", [])]
        
        _LOGGER.debug(f"Datakom: Starting cleanup. Current param_ids: {current_param_ids}")
        
        # Получаем все entity для этой интеграции
        entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
        
        _LOGGER.debug(f"Datakom: Found {len(entities)} total entities for this integration")
        
        # Список правильных unique_id для binary_sensor и button
        valid_binary_sensor_ids = {
            "datakom_health",
            "datakom_led_mains", "datakom_led_genset", "datakom_led_auto", "datakom_led_manual", 
            "datakom_led_test", "datakom_led_run", "datakom_led_stop", "datakom_led_alarm",
            "datakom_alarm_shutdown", "datakom_alarm_loaddump", "datakom_alarm_warning",
            "datakom_led_auto_ready", "datakom_led_mcb", "datakom_led_gcb",
            "datakom_led_mains_fail", "datakom_led_prog1", "datakom_led_prog2"
        }
        valid_sensor_ids = {
            "datakom_data_age", "datakom_fuel_level_smoothed", "datakom_fuel_rate_calc", "datakom_fuel_time_left",
        }
        if entry.data.get("control_key"):
            valid_sensor_ids.add("datakom_control_command")
        valid_button_ids = {"datakom_refresh"}
        valid_switch_ids = set()
        if entry.data.get("control_key"):
            valid_button_ids |= {
                f"datakom_control_{a}" for a in ("stop", "auto", "manual", "test", "run", "service1_reset")
            }
            try:
                valid_switch_ids = {f"datakom_user_output_{n}" for n in parse_user_outputs(entry.data.get("user_outputs"))}
            except ValueError:
                pass
        
        removed_count = 0
        for entity in entities:
            should_remove = False
            
            if entity.domain == "sensor":
                # Для sensor: удаляем если unique_id не в формате datakom_{число} или число не в param_ids
                if entity.unique_id in valid_sensor_ids:
                    pass
                elif entity.unique_id.startswith("datakom_"):
                    parts = entity.unique_id.split("_", 1)
                    if len(parts) == 2 and parts[1].isdigit():
                        param_id = int(parts[1])
                        if param_id not in current_param_ids:
                            should_remove = True
                            _LOGGER.debug(f"Datakom: Will remove sensor {entity.entity_id} - param_id {param_id} not in config")
                    else:
                        # Старый формат типа datakom_engine_coolant_temp
                        should_remove = True
                        _LOGGER.debug(f"Datakom: Will remove sensor {entity.entity_id} - old name format")
                    
            elif entity.domain == "binary_sensor":
                # Для binary_sensor: удаляем если unique_id не в списке правильных или имеет старый prefix
                if entity.unique_id not in valid_binary_sensor_ids:
                    should_remove = True
                    _LOGGER.debug(f"Datakom: Will remove binary_sensor {entity.entity_id} - not in valid list")
                    
            elif entity.domain == "switch":
                if entity.unique_id not in valid_switch_ids:
                    should_remove = True
                    _LOGGER.debug(f"Datakom: Will remove switch {entity.entity_id} - output not configured")

            elif entity.domain == "button":
                # Для button: удаляем если unique_id не в списке правильных или имеет старый prefix
                if entity.unique_id not in valid_button_ids:
                    should_remove = True
                    _LOGGER.debug(f"Datakom: Will remove button {entity.entity_id} - not in valid list")
            
            if should_remove:
                _LOGGER.info(f"Datakom: Removing old entity {entity.entity_id} (unique_id={entity.unique_id})")
                entity_registry.async_remove(entity.entity_id)
                removed_count += 1
        
        if removed_count > 0:
            _LOGGER.info(f"Datakom: Removed {removed_count} old entities")
        else:
            _LOGGER.debug(f"Datakom: No old entities to remove")
    except Exception as e:
        _LOGGER.error(f"Datakom: Error during entity cleanup: {e}", exc_info=True)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry
) -> bool:
    """Remove a config entry from a device."""
    return True
