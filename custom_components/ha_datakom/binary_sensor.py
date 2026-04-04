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
    device_name = entry_data.get("device_name", "Datakom Device")
    update_interval = entry_data.get("update_interval", 5)
    
    _LOGGER.debug(f"Datakom Binary Sensor: Setting up with entry_data: {entry_data}")
    
    if not api_url:
        _LOGGER.error(f"Datakom Binary Sensor: missing api_url: {api_url}")
        return
    
    sensors = []
    
    # Создаём вычисляемые LED binary sensors
    # Endpoint /dump_devm_leds больше не существует, LED вычисляются из параметров
    led_types = ["mains", "genset", "auto", "manual", "test", "run", "stop", "alarm"]
    for led_type in led_types:
        led_sensor = DatakomLedBinarySensor(api_url, led_type, device_name, update_interval)
        sensors.append(led_sensor)
        _LOGGER.debug(f"Datakom: Created calculated LED binary sensor {led_sensor.unique_id}")
    
    # Добавляем binary sensor статуса подключения
    health_sensor = DatakomHealthBinarySensor(api_url, device_name, update_interval)
    sensors.append(health_sensor)
    _LOGGER.debug(f"Datakom: Created health binary sensor {health_sensor.unique_id}")
    
    # Добавляем alarm binary sensors
    alarm_types = ["ShutDown", "LoadDump", "Warning"]
    for alarm_type in alarm_types:
        alarm_sensor = DatakomAlarmBinarySensor(api_url, alarm_type, device_name, update_interval)
        sensors.append(alarm_sensor)
        _LOGGER.debug(f"Datakom: Created alarm binary sensor {alarm_sensor.unique_id}")
    
    if sensors:
        _LOGGER.info(f"Datakom Binary Sensor: Adding {len(sensors)} sensors")
        async_add_entities(sensors, True)
    else:
        _LOGGER.warning("Datakom Binary Sensor: No sensors were created")


class DatakomHealthBinarySensor(BinarySensorEntity):
    """Binary sensor для мониторинга состояния подключения к API Datakom."""

    def __init__(self, api_url, device_name, update_interval):
        self._api_url = api_url
        self._device_name = device_name
        self._attr_has_entity_name = True
        self._attr_name = "API Connection"
        self._attr_unique_id = "datakom_health"
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
        return status == "ok" or listener_running == True

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

    async def async_update(self) -> None:
        # Запрос к /health
        url = f"{self._api_url}/health"
        _LOGGER.debug(f"Datakom: requesting health status from {url}")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=15) as resp:
                    # Проверяем HTTP статус
                    if resp.status != 200:
                        text = await resp.text()
                        _LOGGER.warning(f"Datakom: health endpoint returned status {resp.status}: {text[:200]}")
                        self._status = "Error"
                        self._health_data = {}
                        return
                    
                    # Проверяем content-type
                    content_type = resp.content_type
                    if content_type and 'json' not in content_type:
                        text = await resp.text()
                        _LOGGER.warning(f"Datakom: health endpoint returned non-JSON content-type '{content_type}': {text[:200]}")
                        self._status = "Error"
                        self._health_data = {}
                        return
                    
                    # Пытаемся распарсить JSON
                    try:
                        data = await resp.json()
                        _LOGGER.debug(f"Datakom: health response: {data}")
                        # Сохраняем все данные из ответа
                        self._health_data = data
                        # Сохраняем connect_state для информации (не для проверки is_on)
                        self._status = data.get("connect_state", "Unknown")
                        self._time = data.get("time", "")
                    except ValueError as json_err:
                        text = await resp.text()
                        _LOGGER.warning(f"Datakom: health endpoint returned invalid JSON: {text[:200]}")
                        self._status = "Error"
                        self._health_data = {}
            except Exception as e:
                _LOGGER.error(f"Datakom: health sensor {self._attr_unique_id} update request error: {e}")
                self._status = "Error"
                self._health_data = {}


class DatakomLedBinarySensor(BinarySensorEntity):
    """Binary sensor для отображения состояния LED индикатора Datakom."""

    def __init__(self, api_url, led_name, device_name, update_interval):
        self._api_url = api_url
        self._led_name = led_name
        self._device_name = device_name
        self._attr_has_entity_name = True
        self._attr_name = f"{led_name}"
        self._attr_unique_id = f"datakom_led_{led_name.lower()}"
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
            "description": f"LED indicator status for {self._led_name}",
        }
    
    async def _update_alarm_state(self) -> None:
        """Проверяет наличие активных алармов для LED alarm."""
        url = f"{self._api_url}/dump_devm_alarm"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15) as resp:
                    data = await resp.json()
                    if data.get("success") and "alarm" in data:
                        alarm_data = data["alarm"]
                        # Проверяем есть ли хоть один активный аларм
                        has_alarms = (
                            len(alarm_data.get("ShutDown", [])) > 0 or
                            len(alarm_data.get("LoadDump", [])) > 0 or
                            len(alarm_data.get("Warning", [])) > 0
                        )
                        self._state = 1 if has_alarms else 0
                    else:
                        self._state = 0
        except Exception as e:
            _LOGGER.error(f"Datakom: Alarm check for LED failed: {e}")
            self._state = 0

    async def async_update(self) -> None:
        # Вычисляем состояние LED из параметров dump_devm
        # Endpoint /dump_devm_leds больше не существует
        url = f"{self._api_url}/dump_devm"
        _LOGGER.debug(f"Datakom: requesting parameters for LED calculation from {url}")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=15) as resp:
                    # Проверяем HTTP статус
                    if resp.status != 200:
                        text = await resp.text()
                        _LOGGER.warning(f"Datakom: dump_devm endpoint returned status {resp.status}: {text[:200]}")
                        return  # Оставляем последнее состояние
                    
                    # Проверяем content-type
                    content_type = resp.content_type
                    if content_type and 'json' not in content_type:
                        text = await resp.text()
                        _LOGGER.warning(f"Datakom: dump_devm endpoint returned non-JSON content-type '{content_type}': {text[:200]}")
                        return  # Оставляем последнее состояние
                    
                    # Пытаемся распарсить JSON
                    try:
                        data = await resp.json()
                        _LOGGER.debug(f"Datakom: dump_devm response: {data}")
                    except ValueError as json_err:
                        text = await resp.text()
                        _LOGGER.warning(f"Datakom: dump_devm endpoint returned invalid JSON: {text[:200]}")
                        return  # Оставляем последнее состояние
                    
                    if data.get("success") and "result" in data:
                        params = {str(p["id"]): p.get("value") for p in data["result"]}
                        
                        # ID параметров (из примера API):
                        # 103 = Genset Mode
                        # 105 = Genset State
                        genset_mode = params.get("103", 0)
                        genset_state = params.get("105", 0)
                        
                        # Вычисляем состояние LED в зависимости от типа
                        if self._led_name == "mains":
                            # Mains горит когда генератор НЕ работает (at_rest)
                            self._state = 1 if genset_state == 0 else 0
                        elif self._led_name == "genset":
                            # Genset горит когда генератор работает (не at_rest)
                            self._state = 1 if genset_state != 0 else 0
                        elif self._led_name == "auto":
                            # Auto горит когда режим = AUTO (1) или AUTO_START (4)
                            self._state = 1 if genset_mode in [1, 4] else 0
                        elif self._led_name == "manual":
                            # Manual горит когда режим = MANUAL (2)
                            self._state = 1 if genset_mode == 2 else 0
                        elif self._led_name == "test":
                            # Test горит когда режим = TEST (3)
                            self._state = 1 if genset_mode == 3 else 0
                        elif self._led_name == "run":
                            # Run горит когда генератор работает (state != 0)
                            self._state = 1 if genset_state != 0 else 0
                        elif self._led_name == "stop":
                            # Stop горит когда режим = STOP (0)
                            self._state = 1 if genset_mode == 0 else 0
                        elif self._led_name == "alarm":
                            # Alarm горит если есть активные алармы
                            # Проверяем через отдельный запрос к alarm endpoint
                            await self._update_alarm_state()
                        else:
                            self._state = 0
                    else:
                        _LOGGER.error(f"Datakom: LED calculation failed, response: {data}")
                        self._state = 0
            except Exception as e:
                _LOGGER.error(f"Datakom: LED sensor {self._attr_unique_id} update request error: {e}")
                self._state = 0


class DatakomAlarmBinarySensor(BinarySensorEntity):
    """Binary sensor для отображения состояния алармов Datakom."""

    def __init__(self, api_url, alarm_type, device_name, update_interval):
        self._api_url = api_url
        self._alarm_type = alarm_type
        self._device_name = device_name
        self._attr_has_entity_name = True
        self._attr_name = f"Alarm {alarm_type}"
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
        self._update_interval = update_interval
        self._attr_should_poll = True

    @property
    def scan_interval(self) -> timedelta:
        """Return the scan interval in minutes."""
        return timedelta(minutes=self._update_interval)

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

    async def async_update(self) -> None:
        # Запрос к /dump_devm_alarm
        url = f"{self._api_url}/dump_devm_alarm"
        _LOGGER.debug(f"Datakom: requesting alarm status from {url}")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=15) as resp:
                    # Проверяем HTTP статус
                    if resp.status != 200:
                        text = await resp.text()
                        _LOGGER.warning(f"Datakom: dump_devm_alarm endpoint returned status {resp.status}: {text[:200]}")
                        return  # Оставляем последнее состояние
                    
                    # Проверяем content-type
                    content_type = resp.content_type
                    if content_type and 'json' not in content_type:
                        text = await resp.text()
                        _LOGGER.warning(f"Datakom: dump_devm_alarm endpoint returned non-JSON content-type '{content_type}': {text[:200]}")
                        return  # Оставляем последнее состояние
                    
                    # Пытаемся распарсить JSON
                    try:
                        data = await resp.json()
                        _LOGGER.debug(f"Datakom: alarm response: {data}")
                    except ValueError as json_err:
                        text = await resp.text()
                        _LOGGER.warning(f"Datakom: dump_devm_alarm endpoint returned invalid JSON: {text[:200]}")
                        return  # Оставляем последнее состояние
                    
                    if data.get("success") and "alarm" in data:
                        alarm_data = data["alarm"]
                        alarms_list = alarm_data.get(self._alarm_type, [])
                        # Новый формат: алармы - это объекты с полями slot, name, index
                        if alarms_list and isinstance(alarms_list[0], dict):
                            self._alarms = [alarm.get("name", "").strip() for alarm in alarms_list if alarm.get("name", "").strip()]
                        else:
                            # Старый формат: строки
                            self._alarms = [alarm.strip() for alarm in alarms_list if isinstance(alarm, str) and alarm.strip()]
                    else:
                        _LOGGER.error(f"Datakom: Alarm status failed, response: {data}")
                        self._alarms = []
            except Exception as e:
                _LOGGER.error(f"Datakom: Alarm sensor {self._attr_unique_id} update request error: {e}")
                self._alarms = []
