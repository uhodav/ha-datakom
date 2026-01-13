"""Платформа binary sensor для Datakom интеграции (REST API)."""
import logging
import aiohttp
from datetime import timedelta

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.helpers.entity import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
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
    node_id = entry_data.get("node_id", "")
    device_id = entry_data.get("device_id", "")
    device_name = entry_data.get("device_name", "Datakom Device")
    update_interval = entry_data.get("update_interval", 5)
    
    _LOGGER.debug(f"Datakom Binary Sensor: Setting up with entry_data: {entry_data}")
    
    if not api_url or not device_id or not node_id:
        _LOGGER.error(f"Datakom Binary Sensor: missing config data. api_url={api_url}, node_id={node_id}, device_id={device_id}")
        return
    
    sensors = []
    
    # Получаем список LED индикаторов
    led_names = []
    url = f"{api_url}/dump_devm_leds?did={device_id}&node_id={node_id}"
    _LOGGER.debug(f"Datakom: requesting LED list from {url}")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=15) as resp:
                text = await resp.text()
                _LOGGER.debug(f"Datakom: LED list response: {text}")
                data = await resp.json()
                if data.get("success") and "leds" in data:
                    led_names = list(data["leds"].keys())
                    _LOGGER.debug(f"Datakom: Found LEDs: {led_names}")
                else:
                    _LOGGER.error(f"Datakom: LED list failed, response: {data}")
        except Exception as e:
            _LOGGER.error(f"Datakom: LED list request error: {e}")
    
    # Создаём LED binary sensors
    for led_name in led_names:
        led_sensor = DatakomLedBinarySensor(api_url, node_id, device_id, led_name, device_name, update_interval)
        sensors.append(led_sensor)
        _LOGGER.debug(f"Datakom: Created LED binary sensor {led_sensor.unique_id}")
    
    # Добавляем binary sensor статуса подключения
    health_sensor = DatakomHealthBinarySensor(api_url, node_id, device_id, device_name, update_interval)
    sensors.append(health_sensor)
    _LOGGER.debug(f"Datakom: Created health binary sensor {health_sensor.unique_id}")
    
    # Добавляем alarm binary sensors
    alarm_types = ["ShutDown", "LoadDump", "Warning"]
    for alarm_type in alarm_types:
        alarm_sensor = DatakomAlarmBinarySensor(api_url, node_id, device_id, alarm_type, device_name, update_interval)
        sensors.append(alarm_sensor)
        _LOGGER.debug(f"Datakom: Created alarm binary sensor {alarm_sensor.unique_id}")
    
    if sensors:
        _LOGGER.info(f"Datakom Binary Sensor: Adding {len(sensors)} sensors")
        async_add_entities(sensors, True)
    else:
        _LOGGER.warning("Datakom Binary Sensor: No sensors were created")


class DatakomHealthBinarySensor(BinarySensorEntity):
    """Binary sensor для мониторинга состояния подключения к API Datakom."""

    def __init__(self, api_url, node_id, device_id, device_name, update_interval):
        self._api_url = api_url
        self._node_id = node_id
        self._device_id = device_id
        self._device_name = device_name
        self._attr_has_entity_name = True
        self._attr_name = "API Connection"
        self._attr_unique_id = f"datakom_{node_id}_{device_id}_health"
        self._attr_translation_key = "api_connection"
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._status = None
        self._time = None
        self._health_data = {}
        self._update_interval = update_interval
        self._attr_should_poll = True

    @property
    def scan_interval(self) -> timedelta:
        """Return the scan interval in minutes."""
        return timedelta(minutes=self._update_interval)

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, str(self._device_id))},
            "name": self._device_name,
            "manufacturer": "Datakom",
            "model": "Device",
        }

    @property
    def is_on(self) -> bool:
        """Return true if connected."""
        return self._status == "Connected"

    @property
    def extra_state_attributes(self) -> dict:
        # Определяем цвет: зеленый если подключено, красный если отключено
        if self._status == "Connected":
            icon_color = "green"
            rgb_color = [0, 255, 0]
        else:
            icon_color = "red"
            rgb_color = [255, 0, 0]
            
        attrs = {
            "device_id": self._device_id,
            "node_id": self._node_id,
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

    async def async_update(self) -> None:
        # Запрос к /health
        url = f"{self._api_url}/health"
        _LOGGER.debug(f"Datakom: requesting health status from {url}")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=15) as resp:
                    text = await resp.text()
                    _LOGGER.debug(f"Datakom: health response: {text}")
                    data = await resp.json()
                    # Сохраняем все данные из ответа
                    self._health_data = data
                    self._status = data.get("connect_state", "Unknown")
                    self._time = data.get("time", "")
            except Exception as e:
                _LOGGER.error(f"Datakom: health sensor {self._attr_unique_id} update request error: {e}")
                self._status = "Error"
                self._health_data = {}


class DatakomLedBinarySensor(BinarySensorEntity):
    """Binary sensor для отображения состояния LED индикатора Datakom."""

    def __init__(self, api_url, node_id, device_id, led_name, device_name, update_interval):
        self._api_url = api_url
        self._node_id = node_id
        self._device_id = device_id
        self._led_name = led_name
        self._device_name = device_name
        self._attr_has_entity_name = True
        self._attr_name = f"{led_name}"
        self._attr_unique_id = f"datakom_{node_id}_{device_id}_led_{led_name.lower()}"
        # Устанавливаем translation_key для известных LED
        led_key = led_name.lower().replace(" ", "_").replace("-", "_")
        if led_key in ["mains", "genset", "auto", "manual", "run", "stop", "test"]:
            self._attr_translation_key = led_key
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._state = None
        self._update_interval = update_interval
        self._attr_should_poll = True

    @property
    def scan_interval(self) -> timedelta:
        """Return the scan interval in minutes."""
        return timedelta(minutes=self._update_interval)

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, str(self._device_id))},
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
            "device_id": self._device_id,
            "node_id": self._node_id,
            "device_name": self._device_name,
            "led_name": self._led_name,
            "raw_value": self._state,
            "description": f"LED indicator status for {self._led_name}",
        }

    async def async_update(self) -> None:
        # Запрос к /dump_devm_leds
        url = f"{self._api_url}/dump_devm_leds?did={self._device_id}&node_id={self._node_id}"
        _LOGGER.debug(f"Datakom: requesting LED status from {url}")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=15) as resp:
                    text = await resp.text()
                    _LOGGER.debug(f"Datakom: LED response: {text}")
                    data = await resp.json()
                    if data.get("success") and "leds" in data:
                        leds = data["leds"]
                        self._state = leds.get(self._led_name)
                    else:
                        _LOGGER.error(f"Datakom: LED status failed, response: {data}")
            except Exception as e:
                _LOGGER.error(f"Datakom: LED sensor {self._attr_unique_id} update request error: {e}")
                self._state = None


class DatakomAlarmBinarySensor(BinarySensorEntity):
    """Binary sensor для отображения состояния алармов Datakom."""

    def __init__(self, api_url, node_id, device_id, alarm_type, device_name, update_interval):
        self._api_url = api_url
        self._node_id = node_id
        self._device_id = device_id
        self._alarm_type = alarm_type
        self._device_name = device_name
        self._attr_has_entity_name = True
        self._attr_name = f"Alarm {alarm_type}"
        self._attr_unique_id = f"datakom_{node_id}_{device_id}_alarm_{alarm_type.lower()}"
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
        self._update_interval = update_interval
        self._attr_should_poll = True

    @property
    def scan_interval(self) -> timedelta:
        """Return the scan interval in minutes."""
        return timedelta(minutes=self._update_interval)

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, str(self._device_id))},
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
            "device_id": self._device_id,
            "node_id": self._node_id,
            "device_name": self._device_name,
            "alarm_type": self._alarm_type,
            "alarm_count": len(self._alarms),
            "alarms": self._alarms,
            "icon_color": icon_color,
            "rgb_color": rgb_color,
            "description": f"{self._alarm_type} alarms from device",
        }

    async def async_update(self) -> None:
        # Запрос к /dump_devm_alarm
        url = f"{self._api_url}/dump_devm_alarm?did={self._device_id}&node_id={self._node_id}"
        _LOGGER.debug(f"Datakom: requesting alarm status from {url}")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=15) as resp:
                    text = await resp.text()
                    _LOGGER.debug(f"Datakom: alarm response: {text}")
                    data = await resp.json()
                    if data.get("success") and "alarm" in data:
                        alarm_data = data["alarm"]
                        self._alarms = alarm_data.get(self._alarm_type, [])
                        # Очищаем пробелы в сообщениях аларма
                        self._alarms = [alarm.strip() for alarm in self._alarms if alarm.strip()]
                    else:
                        _LOGGER.error(f"Datakom: Alarm status failed, response: {data}")
                        self._alarms = []
            except Exception as e:
                _LOGGER.error(f"Datakom: Alarm sensor {self._attr_unique_id} update request error: {e}")
                self._alarms = []
