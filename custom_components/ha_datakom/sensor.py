"""Платформа сенсора для Datakom интеграции (REST API)."""
import logging
import aiohttp
from datetime import timedelta, datetime
from zoneinfo import ZoneInfo

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.helpers.entity import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.util import dt as dt_util

from . import DOMAIN, FUEL_DEFAULTS

_LOGGER = logging.getLogger(__name__)

# Маппинг режимов генератора (число -> текстовый ключ)
# Значения регистра Modbus 10605 "Unit mode" (битовая маска)
GENSET_MODE_MAP = {
    "1": "stop", "2": "manual", "4": "auto", "8": "test",
    1: "stop", 2: "manual", 4: "auto", 8: "test",
}

# Маппинг состояния генератора
GENSET_STATE_MAP = {
    "0": "at_rest", "1": "wait_before_fuel", "2": "engine_preheat", "3": "wait_oil_flash_off",
    "4": "crank_rest", "5": "cranking", "6": "engine_run_idle", "7": "engine_heating",
    "8": "running_off_load", "9": "synchronizing_to_mains", "10": "load_transfer_to_genset",
    "11": "gen_cb_activation", "12": "genset_cb_timer", "13": "master_genset_on_load",
    "14": "peak_lopping", "15": "power_exporting", "16": "slave_genset_on_load",
    "17": "synchronizing_back_to_mains", "18": "load_transfer_to_mains", "19": "mains_cb_activation",
    "20": "mains_cb_timer", "21": "stop_with_cooldown", "22": "cooling_down",
    "23": "engine_stop_idle", "24": "immediate_stop", "25": "engine_stopping",
    0: "at_rest", 1: "wait_before_fuel", 2: "engine_preheat", 3: "wait_oil_flash_off",
    4: "crank_rest", 5: "cranking", 6: "engine_run_idle", 7: "engine_heating",
    8: "running_off_load", 9: "synchronizing_to_mains", 10: "load_transfer_to_genset",
    11: "gen_cb_activation", 12: "genset_cb_timer", 13: "master_genset_on_load",
    14: "peak_lopping", 15: "power_exporting", 16: "slave_genset_on_load",
    17: "synchronizing_back_to_mains", 18: "load_transfer_to_mains", 19: "mains_cb_activation",
    20: "mains_cb_timer", 21: "stop_with_cooldown", 22: "cooling_down",
    23: "engine_stop_idle", 24: "immediate_stop", 25: "engine_stopping",
}

# Маппинг состояния двигателя
ENGINE_STATE_MAP = {
    "0": "off", "1": "cranking", "2": "running", "3": "stopping",
    "4": "failed_start", "5": "stalled", "6": "oil_pressure_low",
    "7": "high_temperature", "8": "overspeed",
    0: "off", 1: "cranking", 2: "running", 3: "stopping",
    4: "failed_start", 5: "stalled", 6: "oil_pressure_low",
    7: "high_temperature", 8: "overspeed",
}

# Маппинг состояния выключателей
BREAKER_STATE_MAP = {
    "0": "both_open", "1": "genset_closed",
    "2": "mains_closed", "3": "both_closed",
    0: "both_open", 1: "genset_closed",
    2: "mains_closed", 3: "both_closed",
}

# Маппинг состояния сети
MAINS_STATE_MAP = {
    "0": "ok", "1": "fail", "2": "restore_wait",
    "3": "return_delay", "4": "transfer_to_genset",
    "5": "transfer_to_mains",
    0: "ok", 1: "fail", 2: "restore_wait",
    3: "return_delay", 4: "transfer_to_genset",
    5: "transfer_to_mains",
}

# Маппинг состояния батареи
BATTERY_STATE_MAP = {
    "0": "normal", "1": "low", "2": "critical",
    "3": "disconnected", "4": "charging",
    0: "normal", 1: "low", 2: "critical",
    3: "disconnected", 4: "charging",
}

# Маппинг источника запуска
START_SOURCE_MAP = {
    "0": "none", "1": "manual", "2": "ats_mains_fail",
    "3": "remote", "4": "schedule", "5": "load_demand", "6": "test",
    0: "none", 1: "manual", 2: "ats_mains_fail",
    3: "remote", 4: "schedule", 5: "load_demand", 6: "test",
}

# Маппинг типа работы
RUNNING_TYPE_MAP = {
    "0": "no_load", "1": "on_load", "2": "test", "3": "maintenance",
    0: "no_load", 1: "on_load", 2: "test", 3: "maintenance",
}

# Маппинг состояния зарядки (битовые флаги)
CHARGE_STATE_MAP = {
    "0": "idle", "1": "charging", "2": "float", "3": "equalize",
    "4": "boost", "8": "bulk", "16": "absorption", "32": "error",
    "2048": "unknown",
    0: "idle", 1: "charging", 2: "float", 3: "equalize",
    4: "boost", 8: "bulk", 16: "absorption", 32: "error",
    2048: "unknown",
}

# Тип ENUM по ID параметра API (не зависит от языка названия)
ENUM_BY_PARAM_ID = {"103": "genset_mode", "105": "genset_state", "624": "charge_state"}

# Словарь для сопоставления ключевых слов с маппингами
ENUM_MAPPINGS = {
    "genset_mode": (GENSET_MODE_MAP, ["stop", "manual", "auto", "test"]),
    "genset_state": (GENSET_STATE_MAP, [
        "at_rest", "wait_before_fuel", "engine_preheat", "wait_oil_flash_off",
        "crank_rest", "cranking", "engine_run_idle", "engine_heating",
        "running_off_load", "synchronizing_to_mains", "load_transfer_to_genset",
        "gen_cb_activation", "genset_cb_timer", "master_genset_on_load",
        "peak_lopping", "power_exporting", "slave_genset_on_load",
        "synchronizing_back_to_mains", "load_transfer_to_mains", "mains_cb_activation",
        "mains_cb_timer", "stop_with_cooldown", "cooling_down",
        "engine_stop_idle", "immediate_stop", "engine_stopping"
    ]),
    "engine_state": (ENGINE_STATE_MAP, ["off", "cranking", "running", "stopping", "failed_start", "stalled", "oil_pressure_low", "high_temperature", "overspeed"]),
    "breaker_state": (BREAKER_STATE_MAP, ["both_open", "genset_closed", "mains_closed", "both_closed"]),
    "mains_state": (MAINS_STATE_MAP, ["ok", "fail", "restore_wait", "return_delay", "transfer_to_genset", "transfer_to_mains"]),
    "battery_state": (BATTERY_STATE_MAP, ["normal", "low", "critical", "disconnected", "charging"]),
    "start_source": (START_SOURCE_MAP, ["none", "manual", "ats_mains_fail", "remote", "schedule", "load_demand", "test"]),
    "running_type": (RUNNING_TYPE_MAP, ["no_load", "on_load", "test", "maintenance"]),
    "charge_state": (CHARGE_STATE_MAP, ["idle", "charging", "float", "equalize", "boost", "bulk", "absorption", "error", "unknown"]),
}

# Маппинг единиц измерения на иконки
UNIT_ICONS = {
    "": "mdi:gauge",
    "%": "mdi:percent",
    "'C": "mdi:thermometer",
    "A": "mdi:current-ac",
    "Bar": "mdi:gauge-low",
    "BIN": "mdi:code-brackets",
    "HEX": "mdi:code-brackets",
    "Hz": "mdi:sine-wave",
    "RPM": "mdi:rotate-right",
    "V": "mdi:lightning-bolt",
    "Vdc": "mdi:lightning-bolt",
    "kVAr": "mdi:flash",
    "kVArh": "mdi:flash",
    "kWh": "mdi:counter",
    "kVA": "mdi:flash",
    "kW": "mdi:flash",
    "lt.": "mdi:water",
    "hour": "mdi:clock-outline",
    "day": "mdi:calendar",
    "UTC+00:00": "mdi:clock-outline",
    "~G": "mdi:information",
    "~I": "mdi:information",
    "~M": "mdi:information",
    "~S": "mdi:information",
    "VER": "mdi:information-variant",
}

# Единицы API -> (единица HA, device_class, state_class)
UNIT_MAP = {
    "'C": ("°C", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
    "V": ("V", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT),
    "Vdc": ("V", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT),
    "A": ("A", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT),
    "Hz": ("Hz", SensorDeviceClass.FREQUENCY, SensorStateClass.MEASUREMENT),
    "kW": ("kW", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
    "kVA": ("kVA", None, SensorStateClass.MEASUREMENT),
    "kVAr": ("kvar", None, SensorStateClass.MEASUREMENT),
    "kWh": ("kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    "kVArh": ("kvarh", None, SensorStateClass.TOTAL_INCREASING),
    "Bar": ("bar", SensorDeviceClass.PRESSURE, SensorStateClass.MEASUREMENT),
    "%": ("%", None, SensorStateClass.MEASUREMENT),
    "RPM": ("rpm", None, SensorStateClass.MEASUREMENT),
    "hour": ("h", SensorDeviceClass.DURATION, SensorStateClass.MEASUREMENT),
    "day": ("d", SensorDeviceClass.DURATION, SensorStateClass.MEASUREMENT),
    "lt.": ("L", SensorDeviceClass.VOLUME_STORAGE, SensorStateClass.MEASUREMENT),
    "lt./h": ("L/h", None, SensorStateClass.MEASUREMENT),
    "Ah": ("Ah", None, SensorStateClass.TOTAL_INCREASING),
}

# Счетчики (запуски, прокрутки, моточасы, расход топлива)
TOTAL_INCREASING_IDS = {"503", "507", "511", "577", "598", "608"}

# Параметры API для расчёта топлива
PARAM_GENSET_STATE = "105"
PARAM_GENSET_KVA = "225"  # Загальна повна потужність генератора
PARAM_MAINS_KVA = "169"   # Загальна повна потужність мережі
PARAM_FUEL_LITERS = "585"  # Статус палива (остаток, л)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Настройка платформы сенсора через config entry."""
    entry_data = entry.data
    api_url = entry_data.get("api_url", "")
    device_name = entry_data.get("device_name", "Datakom Device")
    param_ids = entry_data.get("param_ids", [])
    update_interval = entry_data.get("update_interval", 5)
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
    _LOGGER.debug(f"Datakom: Setting up sensors with entry_data: {entry_data}")
    
    if not api_url or not param_ids:
        _LOGGER.error(f"Datakom: missing config data. api_url={api_url}, param_ids={param_ids}")
        return
    
    sensors = []
    # Получаем имена параметров
    param_labels = {}
    # Используем язык из конфигурации entry
    language = entry_data.get("language", "uk")
    url = f"{api_url}/dump_devm_param_names?language={language}"
    _LOGGER.debug(f"Datakom: requesting param names from {url}")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=15) as resp:
                text = await resp.text()
                _LOGGER.debug(f"Datakom: param_names response: {text}")
                data = await resp.json()
                if data.get("success") and "params" in data:
                    for p in data["params"]:
                        # Используем title (перевод) если доступен, иначе label
                        param_labels[str(p["id"])] = p.get("title") or p["label"]
                else:
                    _LOGGER.error(f"Datakom: param_names failed, response: {data}")
        except Exception as e:
            _LOGGER.error(f"Datakom: param_names request error: {e}")
    
    # Создаём сенсоры только для выбранных параметров
    _LOGGER.debug(f"Datakom: Creating sensors for param_ids: {param_ids}")
    for pid in param_ids:
        label = param_labels.get(str(pid), str(pid))
        sensor = DatakomParamSensor(coordinator, pid, label, device_name)
        sensors.append(sensor)
        _LOGGER.debug(f"Datakom: Created sensor {sensor.unique_id} for param {pid}")
    sensors.append(DatakomDataAgeSensor(coordinator, device_name))
    fuel_model = {key: float(entry_data.get(key, default)) for key, default in FUEL_DEFAULTS.items()}
    sensors.append(DatakomFuelRateSensor(coordinator, device_name, fuel_model))
    sensors.append(DatakomFuelTimeSensor(coordinator, device_name, fuel_model))

    if sensors:
        _LOGGER.info(f"Datakom: Adding {len(sensors)} sensors")
        async_add_entities(sensors)
    else:
        _LOGGER.warning("Datakom: No sensors were created")



class DatakomParamSensor(CoordinatorEntity, SensorEntity):
    """Сенсор для одного выбранного параметра Datakom."""

    def __init__(self, coordinator, param_id, label, device_name):
        super().__init__(coordinator)
        self._param_id = param_id
        self._label = label
        self._original_label = label  # Сохраняем оригинальный английский label для description
        self._device_name = device_name
        self._attr_has_entity_name = True
        self._attr_name = label
        self._attr_unique_id = f"datakom_{param_id}"
        
        self.entity_description = SensorEntityDescription(
            key=f"datakom_{param_id}",
            name=label,
        )
        self._state = None
        self._unit = None
        self._label_hint = None
        self._value_hint = None
        self._hass = None
        
        # Автоопределение типа ENUM сенсора: сначала по ID параметра (название может быть
        # переведено - "Режим роботи"), затем по английскому названию
        label_lower = label.lower()
        self._enum_type = ENUM_BY_PARAM_ID.get(str(param_id))
        self._enum_map = None
        
        if self._enum_type:
            pass
        # Genset Mode
        elif "mode" in label_lower and ("genset" in label_lower or "generator" in label_lower):
            self._enum_type = "genset_mode"
        # Genset State
        elif "state" in label_lower and ("genset" in label_lower or "generator" in label_lower):
            self._enum_type = "genset_state"
        # Engine Charge State (проверяем до engine_state для избежания конфликта)
        elif "charge" in label_lower and "state" in label_lower and "engine" in label_lower:
            self._enum_type = "charge_state"
        # Engine State/Status
        elif ("state" in label_lower or "status" in label_lower) and "engine" in label_lower:
            self._enum_type = "engine_state"
        # Breaker/Contactor State
        elif "breaker" in label_lower or "contactor" in label_lower:
            self._enum_type = "breaker_state"
        # Mains State
        elif "state" in label_lower and "mains" in label_lower:
            self._enum_type = "mains_state"
        # Battery State (только для battery, без charge)
        elif ("state" in label_lower or "status" in label_lower) and "battery" in label_lower:
            self._enum_type = "battery_state"
        # Start Source
        elif "start" in label_lower and ("source" in label_lower or "request" in label_lower):
            self._enum_type = "start_source"
        # Running Type
        elif "running" in label_lower and "type" in label_lower:
            self._enum_type = "running_type"
        
        # Применяем настройки ENUM если тип определен
        if self._enum_type and self._enum_type in ENUM_MAPPINGS:
            self._enum_map, options = ENUM_MAPPINGS[self._enum_type]
            self._attr_translation_key = self._enum_type
            self._attr_device_class = SensorDeviceClass.ENUM
            self._attr_options = options

    def _convert_utc_to_local(self, time_str: str) -> str:
        """Преобразует время из UTC в локальный часовой пояс Home Assistant."""
        try:
            # Парсим время в формате HH:MM:SS UTC+00:00
            time_part = time_str.split(" ")[0]  # Получаем только HH:MM:SS
            
            # Получаем текущую дату и создаем datetime с UTC
            now = datetime.now(ZoneInfo("UTC"))
            time_obj = datetime.strptime(time_part, "%H:%M:%S")
            utc_time = datetime(now.year, now.month, now.day, 
                              time_obj.hour, time_obj.minute, time_obj.second,
                              tzinfo=ZoneInfo("UTC"))
            
            # Преобразуем в локальный часовой пояс HA
            if self._hass:
                local_tz = dt_util.get_default_time_zone()
                local_time = utc_time.astimezone(local_tz)
                # Форматируем с часовым поясом
                tz_offset = local_time.strftime("%z")
                formatted_offset = f"UTC{tz_offset[:3]}:{tz_offset[3:]}"
                return f"{local_time.strftime('%H:%M:%S')} {formatted_offset}"
            
            return time_str
        except Exception as e:
            _LOGGER.debug(f"Datakom: Failed to convert time {time_str}: {e}")
            return time_str

    def _get_icon(self) -> str:
        """Получить иконку на основе единицы измерения."""
        if self._unit:
            return UNIT_ICONS.get(self._unit, "mdi:gauge")
        return "mdi:gauge"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "datakom_device")},
            "name": self._device_name,
            "manufacturer": "Datakom",
            "model": "Device",
        }

    @property
    def name(self) -> str:
        return self._attr_name

    @property
    def unique_id(self) -> str:
        return self._attr_unique_id

    @property
    def available(self) -> bool:
        # Устаревшие данные (контроллер не на связи) показываем как недоступные
        data = self.coordinator.data or {}
        return super().available and not data.get("stale", False)

    @property
    def native_value(self):
        # Числовой сенсор не может иметь текстовое значение ("N/A")
        if self.state_class and not isinstance(self._state, (int, float)):
            return None
        return self._state

    @property
    def device_class(self):
        if self._enum_type:
            return SensorDeviceClass.ENUM
        return UNIT_MAP.get(self._unit, (None, None, None))[1]

    @property
    def state_class(self):
        if self._enum_type:
            return None
        if str(self._param_id) in TOTAL_INCREASING_IDS:
            return SensorStateClass.TOTAL_INCREASING
        return UNIT_MAP.get(self._unit, (None, None, None))[2]

    @property
    def icon(self) -> str:
        return self._get_icon()

    @property
    def native_unit_of_measurement(self):
        # Не показываем unit для временных сенсоров (часовой пояс уже в значении)
        if self._unit == "UTC+00:00":
            return None
        # Не показываем unit для ENUM сенсоров (значение уже текстовое)
        if self._enum_type:
            return None
        # Дополнительная проверка для mode/state сенсоров по unit типу
        if self._unit and self._unit.startswith("~"):
            return None
        return UNIT_MAP.get(self._unit, (self._unit or None,))[0]

    @property
    def extra_state_attributes(self) -> dict:
        attrs = {
            "unique_id": self._attr_unique_id,
            "label": self._label,
            "device_name": self._device_name,
            "param_id": self._param_id,
            "description": f"Parameter sensor for {self._original_label}",
        }
        
        # Добавляем labelHint и valueHint если есть
        if self._label_hint:
            attrs["label_hint"] = self._label_hint
        if self._value_hint:
            attrs["value_hint"] = self._value_hint
            
        return attrs

    def _update_from_coordinator(self) -> None:
        data = self.coordinator.data or {}
        result = list(data.get("params", {}).values())
        for p in result:
            if str(p["id"]) == str(self._param_id):
                value = p.get("value")
                self._unit = p.get("unit", "")
                                
                # Сохраняем оригинальный английский label если доступен
                if "label" in p and p["label"]:
                    self._original_label = p["label"]
                                
                # Обновляем label из title если доступен (с переводом)
                if "title" in p and p["title"]:
                    self._label = p["title"]
                    self._attr_name = p["title"]
                                
                # Сохраняем labelHint и valueHint
                self._label_hint = p.get("labelHint")
                self._value_hint = p.get("valueHint")
                                
                # Если это время с UTC+00:00, преобразуем в локальный часовой пояс
                if self._unit == "UTC+00:00" and value:
                    self._state = self._convert_utc_to_local(value)
                # Если это ENUM сенсор, конвертируем число в текстовый ключ
                elif self._enum_map and value is not None:
                    self._state = self._enum_map.get(str(value), self._enum_map.get(value, str(value)))
                else:
                    self._state = value
                break

    def _handle_coordinator_update(self) -> None:
        self._update_from_coordinator()
        super()._handle_coordinator_update()

    async def async_added_to_hass(self) -> None:
        """Вызывается когда сенсор добавлен в Home Assistant."""
        await super().async_added_to_hass()
        self._hass = self.hass
        self._update_from_coordinator()


class DatakomDataAgeSensor(CoordinatorEntity, SensorEntity):
    """Сколько секунд назад контроллер прислал последнюю телеметрию."""

    def __init__(self, coordinator, device_name):
        super().__init__(coordinator)
        self._device_name = device_name
        self._attr_has_entity_name = True
        self._attr_name = "Data age"
        self._attr_unique_id = "datakom_data_age"
        self._attr_translation_key = "data_age"
        self._attr_device_class = SensorDeviceClass.DURATION
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "s"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_icon = "mdi:timer-sand"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "datakom_device")},
            "name": self._device_name,
            "manufacturer": "Datakom",
            "model": "Device",
        }

    @property
    def native_value(self):
        return (self.coordinator.data or {}).get("data_age_seconds")

    @property
    def extra_state_attributes(self) -> dict:
        data = self.coordinator.data or {}
        return {"stale": data.get("stale"), "telemetry_timestamp": data.get("timestamp")}


class DatakomFuelSensor(CoordinatorEntity, SensorEntity):
    """База расчётных сенсоров топлива (эмпирическая модель расхода от нагрузки)."""

    def __init__(self, coordinator, device_name, fuel_model):
        super().__init__(coordinator)
        self._device_name = device_name
        self._fuel_model = fuel_model
        self._attr_has_entity_name = True
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_suggested_display_precision = 1

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "datakom_device")},
            "name": self._device_name,
            "manufacturer": "Datakom",
            "model": "Device",
        }

    @property
    def available(self) -> bool:
        data = self.coordinator.data or {}
        return super().available and not data.get("stale", False)

    def _param(self, param_id: str):
        """Числовое значение параметра или None."""
        p = (self.coordinator.data or {}).get("params", {}).get(param_id)
        try:
            return float(p.get("value"))
        except (AttributeError, TypeError, ValueError):
            return None

    def _engine_running(self) -> bool:
        state = self._param(PARAM_GENSET_STATE)
        if state is not None:
            return state != 0  # 0 = at_rest
        return (self._param(PARAM_GENSET_KVA) or 0) > 0

    def _rate(self, load_kva: float) -> float:
        """Расход топлива, л/ч, при нагрузке load_kva."""
        m = self._fuel_model
        return max(m["fuel_idle_rate"], m["fuel_slope"] * load_kva - m["fuel_offset"])


class DatakomFuelRateSensor(DatakomFuelSensor):
    """Текущий расход топлива по нагрузке генератора (0, когда двигатель не работает)."""

    def __init__(self, coordinator, device_name, fuel_model):
        super().__init__(coordinator, device_name, fuel_model)
        self._attr_name = "Fuel consumption (calculated)"
        self._attr_unique_id = "datakom_fuel_rate_calc"
        self._attr_translation_key = "fuel_rate_calc"
        self._attr_native_unit_of_measurement = "L/h"
        self._attr_icon = "mdi:fuel"

    @property
    def native_value(self):
        if not self._engine_running():
            return 0.0
        return round(self._rate(self._param(PARAM_GENSET_KVA) or 0), 2)


class DatakomFuelTimeSensor(DatakomFuelSensor):
    """На сколько часов хватит топлива (без резерва) при текущей нагрузке.

    Когда генератор не работает, нагрузку берём с сети - прогноз на случай отключения.
    """

    def __init__(self, coordinator, device_name, fuel_model):
        super().__init__(coordinator, device_name, fuel_model)
        self._attr_name = "Fuel time left"
        self._attr_unique_id = "datakom_fuel_time_left"
        self._attr_translation_key = "fuel_time_left"
        self._attr_device_class = SensorDeviceClass.DURATION
        self._attr_native_unit_of_measurement = "h"
        self._attr_icon = "mdi:timer-sand"

    def _load(self):
        """(нагрузка кВА, источник)."""
        if self._engine_running():
            return self._param(PARAM_GENSET_KVA) or 0, "genset"
        mains = self._param(PARAM_MAINS_KVA)
        if mains is not None:
            return mains, "mains"
        return 0, "none"

    @property
    def native_value(self):
        liters = self._param(PARAM_FUEL_LITERS)
        if liters is None:
            return None
        load, _ = self._load()
        return round(max(0, liters - self._fuel_model["fuel_reserve"]) / self._rate(load), 1)

    @property
    def extra_state_attributes(self) -> dict:
        load, source = self._load()
        return {
            "fuel_liters": self._param(PARAM_FUEL_LITERS),
            "reserve_liters": self._fuel_model["fuel_reserve"],
            "load_kva": load,
            "load_source": source,
            "fuel_rate_l_h": round(self._rate(load), 2),
        }
