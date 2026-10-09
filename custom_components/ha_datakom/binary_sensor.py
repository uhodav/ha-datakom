"""Платформа binary sensor для Datakom интеграции (REST API)."""
import logging
import aiohttp
from datetime import timedelta

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.helpers.entity import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Настройка платформы binary sensor через config entry."""
    entry_data = entry.data
    api_url = entry_data.get("api_url", "")
    device_name = entry_data.get("device_name", "Datakom Device")
    update_interval = entry_data.get("update_interval", 5)
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
    _LOGGER.debug(f"Datakom Binary Sensor: Setting up with entry_data: {entry_data}")
    
    if not api_url:
        _LOGGER.error(f"Datakom Binary Sensor: missing api_url: {api_url}")
        return
    
    sensors = []
    
    # Создаём вычисляемые LED binary sensors
    # Endpoint /dump_devm_leds больше не существует, LED вычисляются из параметров
    led_types = ["mains", "genset", "auto", "manual", "test", "run", "stop", "alarm", "auto_ready", "mcb", "gcb", "mains_fail", "prog1", "prog2"]
    for led_type in led_types:
        led_sensor = DatakomLedBinarySensor(coordinator, led_type, device_name)
        sensors.append(led_sensor)
        _LOGGER.debug(f"Datakom: Created calculated LED binary sensor {led_sensor.unique_id}")
    
    # Добавляем binary sensor статуса подключения
    health_sensor = DatakomHealthBinarySensor(coordinator, device_name)
    sensors.append(health_sensor)
    _LOGGER.debug(f"Datakom: Created health binary sensor {health_sensor.unique_id}")
    
    # Добавляем alarm binary sensors
    alarm_types = ["ShutDown", "LoadDump", "Warning"]
    for alarm_type in alarm_types:
        alarm_sensor = DatakomAlarmBinarySensor(coordinator, alarm_type, device_name)
        sensors.append(alarm_sensor)
        _LOGGER.debug(f"Datakom: Created alarm binary sensor {alarm_sensor.unique_id}")
    
    if sensors:
        _LOGGER.info(f"Datakom Binary Sensor: Adding {len(sensors)} sensors")
        async_add_entities(sensors)
    else:
        _LOGGER.warning("Datakom Binary Sensor: No sensors were created")


class DatakomHealthBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor для мониторинга состояния подключения к API Datakom."""

    def __init__(self, coordinator, device_name):
        super().__init__(coordinator)
        self._device_name = device_name
        self.entity_id = "binary_sensor.datakom_device_api_connection"
        self._attr_has_entity_name = True
        self._attr_unique_id = "datakom_health"
        self._attr_translation_key = "api_connection"
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._status = None
        self._time = None
        self._health_data = {}

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "datakom_device")},
            "name": self._device_name,
            "manufacturer": "Datakom",
            "model": "Device",
        }

    @property
    def is_on(self) -> bool:
        """Return true if connected."""
        # Проверяем status=='ok' или listener_running==true
        status = self._health_data.get("status", "")
        listener_running = self._health_data.get("listener_running", False)
        if (self.coordinator.data or {}).get("stale", True):
            return False
        return status == "ok" or listener_running == True

    @property
    def available(self) -> bool:
        return True

    @property
    def extra_state_attributes(self) -> dict:
        # Определяем цвет: зеленый если подключено, красный если отключено
        status = self._health_data.get("status", "")
        listener_running = self._health_data.get("listener_running", False)
        if status == "ok" or listener_running == True:
            icon_color = "green"
            rgb_color = [0, 255, 0]
        else:
            icon_color = "red"
            rgb_color = [255, 0, 0]
            
        attrs = {
            "device_name": self._device_name,
            "connect_state": self._status,
            "last_update": self._time,
            "icon_color": icon_color,
            "rgb_color": rgb_color,
            "description": "API connection status monitor",
        }
        
        # Добавляем все поля из ответа health endpoint
        for key, value in self._health_data.items():
            if key not in attrs:  # Не перезаписываем уже существующие
                attrs[key] = value
                
        return attrs

    def _update_from_coordinator(self) -> None:
        data = (self.coordinator.data or {}).get("health")
        if data is None:
            self._status = "Error"
            self._health_data = {}
            return
        # Сохраняем все данные из ответа
        self._health_data = data
        # Сохраняем connect_state для информации (не для проверки is_on)
        self._status = data.get("connect_state", "Unknown")
        self._time = data.get("time", "")

    def _handle_coordinator_update(self) -> None:
        self._update_from_coordinator()
        super()._handle_coordinator_update()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._update_from_coordinator()


# LED режима -> значение параметра 103 (Genset Mode, Modbus 10605 Unit mode)
GENSET_MODE_LEDS = {"stop": 1, "manual": 2, "auto": 4, "test": 8}

# LED панели из параметра 117 (байты 117-124 пакета) с номерами битов как в портале Datakom
# (DK_datakom.js, DK_bit_obtain(leds, бит, 2)). 2 бита на LED: 0 - выкл, 1 - жёлтый, 2 - зелёный.
# На D500 RUN использует бит MAN.
PANEL_LEDS = {
    "gcb": 0,
    "mcb": 2,
    "auto_ready": 12,
    "genset": 14,
    "test": 16,
    "manual": 18,
    "run": 18,
    "auto": 20,
    "stop": 22,
    "mains": 24,
    "mains_fail": 26,
    "prog1": 28,
    "prog2": 30,
}


class DatakomLedBinarySensor(CoordinatorEntity, RestoreEntity, BinarySensorEntity):
    """Binary sensor для отображения состояния LED индикатора Datakom."""

    def __init__(self, coordinator, led_name, device_name):
        super().__init__(coordinator)
        self._led_name = led_name
        self._device_name = device_name
        # Имя - из перевода; entity_id фиксирован: на него ссылается карточка datakom-controller-card
        self.entity_id = f"binary_sensor.datakom_device_{led_name}"
        self._attr_has_entity_name = True
        self._attr_unique_id = f"datakom_led_{led_name}"
        self._attr_translation_key = led_name
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._state = None
        self._led_value = None

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "datakom_device")},
            "name": self._device_name,
            "manufacturer": "Datakom",
            "model": "Device",
        }

    @property
    def is_on(self) -> bool:
        """Return true if LED is on."""
        return self._state == 1

    @property
    def icon(self) -> str:
        """Return icon based on LED state."""
        if self._state == 1:
            return "mdi:led-on"
        elif self._state == 0:
            return "mdi:led-off"
        else:
            return "mdi:led-outline"

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "device_name": self._device_name,
            "led_name": self._led_name,
            "raw_value": self._state,
            "led_value": self._led_value,
            "description": f"LED indicator status for {self._led_name}",
        }
    
    def _update_alarm_state(self) -> None:
        """Проверяет наличие активных алармов для LED alarm."""
        alarm_data = (self.coordinator.data or {}).get("alarm") or {}
        # Проверяем есть ли хоть один активный аларм
        has_alarms = (
            len(alarm_data.get("ShutDown", [])) > 0 or
            len(alarm_data.get("LoadDump", [])) > 0 or
            len(alarm_data.get("Warning", [])) > 0
        )
        self._state = 1 if has_alarms else 0

    def _update_from_coordinator(self) -> None:
        data = self.coordinator.data or {}
        if data.get("params"):
            params = {pid: p.get("value") for pid, p in data["params"].items()}
            leds = params.get("117")
            if self._led_name in PANEL_LEDS and isinstance(leds, str) and len(leds) == 16:
                bit = PANEL_LEDS[self._led_name]
                self._led_value = int(leds[bit // 8 * 2:bit // 8 * 2 + 2], 16) >> (bit % 8) & 0b11
                self._state = 1 if self._led_value else 0
                return

            # ID параметров (из примера API):
            # 103 = Genset Mode
            # 105 = Genset State
            genset_mode = params.get("103")
            genset_state = params.get("105", 0)
            
            # Вычисляем состояние LED в зависимости от типа
            if self._led_name == "mains":
                # Mains горит когда генератор НЕ работает (at_rest)
                self._state = 1 if genset_state == 0 else 0
            elif self._led_name == "genset":
                # Genset горит когда генератор работает (не at_rest)
                self._state = 1 if genset_state != 0 else 0
            elif self._led_name == "auto_ready":
                self._state = 1 if genset_mode == GENSET_MODE_LEDS["auto"] else 0
            elif self._led_name in GENSET_MODE_LEDS:
                # Режим (Modbus 10605): 1=STOP, 2=MANUAL, 4=AUTO, 8=TEST
                self._state = 1 if genset_mode == GENSET_MODE_LEDS[self._led_name] else 0
            elif self._led_name == "run":
                # Run - кнопка пуску в ручному режимі: горить лише коли режим MANUAL (2)
                # і двигун працює. В AUTO роботу генератора показує LED genset.
                self._state = 1 if genset_mode == GENSET_MODE_LEDS["manual"] and genset_state != 0 else 0
            elif self._led_name == "alarm":
                # Alarm горит если есть активные алармы
                self._update_alarm_state()
            else:
                self._state = 0
        # Нет данных от API - оставляем последнее состояние

    def _handle_coordinator_update(self) -> None:
        self._update_from_coordinator()
        super()._handle_coordinator_update()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state in ("on", "off"):
            self._state = 1 if last_state.state == "on" else 0
            self._led_value = last_state.attributes.get("led_value")
        self._update_from_coordinator()

    @property
    def available(self) -> bool:
        # Нет связи или данные устарели - показываем последнее состояние
        return True


class DatakomAlarmBinarySensor(CoordinatorEntity, RestoreEntity, BinarySensorEntity):
    """Binary sensor для отображения состояния алармов Datakom."""

    def __init__(self, coordinator, alarm_type, device_name):
        super().__init__(coordinator)
        self._alarm_type = alarm_type
        self._device_name = device_name
        self.entity_id = f"binary_sensor.datakom_device_alarm_{alarm_type.lower()}"
        self._attr_has_entity_name = True
        self._attr_unique_id = f"datakom_alarm_{alarm_type.lower()}"
        # Устанавливаем translation_key для аларма
        alarm_key = f"alarm_{alarm_type.lower()}"
        self._attr_translation_key = alarm_key
        
        # Устанавливаем device_class в зависимости от типа аларма
        if alarm_type == "ShutDown":
            self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        elif alarm_type == "Warning":
            self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        else:
            self._attr_device_class = BinarySensorDeviceClass.PROBLEM
            
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._alarms = []

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "datakom_device")},
            "name": self._device_name,
            "manufacturer": "Datakom",
            "model": "Device",
        }

    @property
    def is_on(self) -> bool:
        """Return true if there are active alarms."""
        return len(self._alarms) > 0

    @property
    def icon(self) -> str:
        """Return icon based on alarm state."""
        if len(self._alarms) > 0:
            if self._alarm_type == "ShutDown":
                return "mdi:alert-octagon"
            elif self._alarm_type == "Warning":
                return "mdi:alert"
            else:
                return "mdi:alert-circle"
        else:
            return "mdi:check-circle"

    @property
    def extra_state_attributes(self) -> dict:
        # Определяем цвет: красный если есть проблема, зеленый если все хорошо
        if len(self._alarms) > 0:
            icon_color = "red"
            rgb_color = [255, 0, 0]
        else:
            icon_color = "green"
            rgb_color = [0, 255, 0]
            
        return {
            "device_name": self._device_name,
            "alarm_type": self._alarm_type,
            "alarm_count": len(self._alarms),
            "alarms": self._alarms,
            "icon_color": icon_color,
            "rgb_color": rgb_color,
            "description": f"{self._alarm_type} alarms from device",
        }

    def _update_from_coordinator(self) -> None:
        alarm_data = (self.coordinator.data or {}).get("alarm")
        if alarm_data is None:
            return  # нет данных от API - оставляем последний список
        alarms_list = alarm_data.get(self._alarm_type, [])
        # Новый формат: алармы - это объекты с полями slot, name, index
        if alarms_list and isinstance(alarms_list[0], dict):
            self._alarms = [alarm.get("name", "").strip() for alarm in alarms_list if alarm.get("name", "").strip()]
        else:
            # Старый формат: строки
            self._alarms = [alarm.strip() for alarm in alarms_list if isinstance(alarm, str) and alarm.strip()]

    def _handle_coordinator_update(self) -> None:
        self._update_from_coordinator()
        super()._handle_coordinator_update()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None and isinstance(last_state.attributes.get("alarms"), list):
            self._alarms = list(last_state.attributes["alarms"])
        self._update_from_coordinator()

    @property
    def available(self) -> bool:
        # Нет связи или данные устарели - показываем последнее состояние
        return True
