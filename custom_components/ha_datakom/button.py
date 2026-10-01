"""Платформа button для Datakom интеграции (REST API)."""
import logging
import aiohttp

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import HomeAssistantError

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Дії, дозволені API за замовчуванням (genset/mains - перемикання навантаження - вимкнені)
CONTROL_ACTIONS = ["stop", "auto", "manual", "test"]


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

    entities = [DatakomRestartButton(api_url, device_name)]
    # Кнопки керування створюються лише коли задано ключ керування (X-API-Key)
    control_key = entry_data.get("control_key", "")
    if control_key:
        entities += [DatakomControlButton(api_url, device_name, action, control_key) for action in CONTROL_ACTIONS]
    async_add_entities(entities)
class DatakomRestartButton(ButtonEntity):
    """Button для перезагрузки устройства Datakom."""

    def __init__(self, api_url, device_name):
        self._api_url = api_url
        self._device_name = device_name
        self._attr_has_entity_name = True
        self._attr_name = "Restart"
        self._attr_unique_id = "datakom_restart"
        self._attr_translation_key = "restart"
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_icon = "mdi:restart"

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
            "description": "Restart the Datakom device",
        }

    async def async_press(self) -> None:
        """Обработка нажатия кнопки перезагрузки."""
        url = f"{self._api_url}/restart"
        _LOGGER.info(f"Datakom: Sending restart command to {url}")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=30) as resp:
                    text = await resp.text()
                    _LOGGER.debug(f"Datakom: restart response: {text}")
                    data = await resp.json()
                    
                    if data.get("success"):
                        _LOGGER.info(f"Datakom: Restart command successful")
                    else:
                        _LOGGER.error(f"Datakom: Restart command failed, response: {data}")
            except Exception as e:
                _LOGGER.error(f"Datakom: Restart button {self._attr_unique_id} request error: {e}")


class DatakomControlButton(ButtonEntity):
    """Button для управления устройством Datakom (Run/Auto/Manual/Test/Stop)."""

    def __init__(self, api_url, device_name, action, control_key):
        self._api_url = api_url
        self._device_name = device_name
        self._action = action
        self._control_key = control_key
        # Фиксированный entity_id: на него ссылается карточка datakom-controller-card
        self.entity_id = f"button.datakom_device_control_{action}"
        self._attr_has_entity_name = True
        self._attr_name = action.capitalize()
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
        """Обработка нажатия кнопки управления."""
        url = f"{self._api_url}/device/control"
        _LOGGER.info(f"Datakom: Sending control command {self._action} to {url}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json={"action": self._action},
                    headers={"X-API-Key": self._control_key},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    data = await resp.json(content_type=None)
        except Exception as e:
            _LOGGER.error(f"Datakom: Control button {self._attr_unique_id} request error: {e}")
            raise HomeAssistantError(f"Datakom: команда {self._action} не відправлена: {e}") from e

        if not data.get("success"):
            _LOGGER.error(f"Datakom: Control command {self._action} failed, response: {data}")
            raise HomeAssistantError(f"Datakom: команда {self._action} не виконана: {data.get('error')}")
        _LOGGER.info(f"Datakom: Control command {self._action} confirmed by controller")
