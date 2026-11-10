"""Платформа button для Datakom интеграции (REST API)."""
import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

from . import DOMAIN
from .control_api import async_send_control

_LOGGER = logging.getLogger(__name__)

# Дії, дозволені API за замовчуванням (genset/mains - перемикання навантаження - вимкнені).
# run - кнопка RUN (пуск двигуна в ручному режимі), service1_reset - скинути лічильники ТО-1 («ТО виконано»)
CONTROL_ACTIONS = ["stop", "auto", "manual", "test", "run", "service1_reset"]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Настройка платформы button через config entry."""
    entry_data = entry.data
    api_url = entry_data.get("api_url", "")
    device_name = entry_data.get("device_name", "Datakom Device")
    
    _LOGGER.debug(f"Datakom Button: Setting up with entry_data: {entry_data}")
    
    if not api_url:
        _LOGGER.error(f"Datakom Button: missing api_url: {api_url}")
        return

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    tracker = hass.data[DOMAIN][entry.entry_id].get("command")
    entities = [DatakomRefreshButton(coordinator, device_name)]
    # Кнопки керування створюються лише коли задано ключ керування (X-API-Key)
    control_key = entry_data.get("control_key", "")
    if control_key:
        entities += [
            DatakomControlButton(api_url, device_name, action, control_key, coordinator, tracker)
            for action in CONTROL_ACTIONS
        ]
    async_add_entities(entities)
class DatakomRefreshButton(ButtonEntity):
    """Button для немедленного обновления данных Datakom."""

    def __init__(self, coordinator, device_name):
        self._coordinator = coordinator
        self._device_name = device_name
        self.entity_id = "button.datakom_device_refresh"
        self._attr_has_entity_name = True
        self._attr_unique_id = "datakom_refresh"
        self._attr_translation_key = "refresh"
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_icon = "mdi:refresh"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "datakom_device")},
            "name": self._device_name,
            "manufacturer": "Datakom",
            "model": "Device",
        }

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "device_name": self._device_name,
            "description": "Refresh Datakom data",
        }

    async def async_press(self) -> None:
        """Обработка нажатия кнопки обновления."""
        await self._coordinator.async_request_refresh()


class DatakomControlButton(ButtonEntity):
    """Button для управления устройством Datakom (Run/Auto/Manual/Test/Stop, скидання ТО-1)."""

    def __init__(self, api_url, device_name, action, control_key, coordinator, tracker=None):
        self._api_url = api_url
        self._coordinator = coordinator
        self._tracker = tracker
        self._device_name = device_name
        self._action = action
        self._control_key = control_key
        # Фиксированный entity_id: на него ссылается карточка datakom-controller-card
        self.entity_id = f"button.datakom_device_control_{action}"
        self._attr_has_entity_name = True
        self._attr_unique_id = f"datakom_control_{action}"
        self._attr_translation_key = f"control_{action}"
        self._attr_entity_category = EntityCategory.CONFIG
        
        # Устанавливаем иконки для каждого действия
        icon_map = {
            "run": "mdi:play",
            "auto": "mdi:auto-fix",
            "manual": "mdi:hand-back-right",
            "test": "mdi:test-tube",
            "stop": "mdi:stop",
            "service1_reset": "mdi:wrench-check",
        }
        self._attr_icon = icon_map.get(action, "mdi:gesture-tap-button")

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "datakom_device")},
            "name": self._device_name,
            "manufacturer": "Datakom",
            "model": "Device",
        }

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "device_name": self._device_name,
            "action": self._action,
            "description": f"Send {self._action} command to the device",
        }

    async def async_press(self) -> None:
        """Обработка нажатия кнопки управления. Ход команды - в sensor.datakom_device_control_command."""
        tracker = self._tracker
        # Та же команда уже отправляется или ждёт в очереди - повторное нажатие ничего не меняет
        if tracker and tracker.action == self._action and tracker.state in ("sending", "queued"):
            _LOGGER.info(f"Datakom: Control command {self._action} already {tracker.state}, press ignored")
            return
        await async_send_control(
            self.hass, self._api_url, self._control_key, {"action": self._action}, self._coordinator, tracker
        )
