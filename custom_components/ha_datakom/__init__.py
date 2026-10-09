import logging
from pathlib import Path
from homeassistant.components.frontend import add_extra_js_url
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.loader import async_get_integration

from .coordinator import DEFAULT_SCAN_INTERVAL, DatakomCoordinator

DOMAIN = "ha_datakom"
_LOGGER = logging.getLogger(__name__)

__all__ = ["DOMAIN", "FUEL_DEFAULTS", "_cleanup_old_entities"]

# Эмпирическая модель расхода топлива: Q = max(idle_rate, slope * P - offset), л/ч (P - полная мощность, кВА).
# reserve - неиспользуемый остаток топлива (л), не учитывается в расчёте времени работы
FUEL_DEFAULTS = {
    "fuel_idle_rate": 2.5,
    "fuel_slope": 1.014,
    "fuel_offset": 17.97,
    "fuel_reserve": 30,
}

# Карточки Lovelace поставляются с интеграцией: файлы из frontend/ отдаются по этому адресу
# и подключаются во фронтенд автоматически, копировать их и добавлять ресурс не нужно
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
    for script in FRONTEND_SCRIPTS:
        add_extra_js_url(hass, f"{FRONTEND_URL}/{script}?v={version}")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
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
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator, "data": entry.data}
    
    # Удаляем старые entity перед созданием новых
    await _cleanup_old_entities(hass, entry)
    
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor", "button"])
    
    return True

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
        valid_sensor_ids = {"datakom_data_age", "datakom_fuel_rate_calc", "datakom_fuel_time_left"}
        valid_button_ids = {"datakom_refresh"}
        if entry.data.get("control_key"):
            valid_button_ids |= {f"datakom_control_{a}" for a in ("stop", "auto", "manual", "test")}
        
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
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor", "binary_sensor", "button"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry
) -> bool:
    """Remove a config entry from a device."""
    return True
