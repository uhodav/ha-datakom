"""Платформа button для Datakom интеграции (REST API)."""
import logging
import aiohttp

from homeassistant.components.button import ButtonEntity
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
    """Настройка платформы button через config entry."""
    entry_data = entry.data
    api_url = entry_data.get("api_url", "")
    node_id = entry_data.get("node_id", "")
    device_id = entry_data.get("device_id", "")
    device_name = entry_data.get("device_name", "Datakom Device")
    
    _LOGGER.debug(f"Datakom Button: Setting up with entry_data: {entry_data}")
    
    if not api_url or not device_id or not node_id:
        _LOGGER.error(f"Datakom Button: missing config data. api_url={api_url}, node_id={node_id}, device_id={device_id}")
        return
    
    buttons = []
    
    # Добавляем кнопку перезагрузки
    restart_button = DatakomRestartButton(api_url, node_id, device_id, device_name)
    buttons.append(restart_button)
    _LOGGER.debug(f"Datakom: Created restart button {restart_button.unique_id}")
    
    # Добавляем кнопки управления устройством
    control_actions = ["run", "auto", "manual", "test", "stop"]
    for action in control_actions:
        control_button = DatakomControlButton(api_url, node_id, device_id, device_name, action)
        buttons.append(control_button)
        _LOGGER.debug(f"Datakom: Created control button {control_button.unique_id} for action {action}")
    
    if buttons:
        _LOGGER.info(f"Datakom Button: Adding {len(buttons)} buttons")
        async_add_entities(buttons, True)
    else:
        _LOGGER.warning("Datakom Button: No buttons were created")


class DatakomRestartButton(ButtonEntity):
    """Button для перезагрузки устройства Datakom."""

    def __init__(self, api_url, node_id, device_id, device_name):
        self._api_url = api_url
        self._node_id = node_id
        self._device_id = device_id
        self._device_name = device_name
        self._attr_name = "Restart"
        self._attr_unique_id = f"datakom_{node_id}_{device_id}_restart"
        self._attr_translation_key = "restart"
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_icon = "mdi:restart"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, str(self._device_id))},
            "name": self._device_name,
            "manufacturer": "Datakom",
            "model": "Device",
        }

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "device_id": self._device_id,
            "node_id": self._node_id,
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

    def __init__(self, api_url, node_id, device_id, device_name, action):
        self._api_url = api_url
        self._node_id = node_id
        self._device_id = device_id
        self._device_name = device_name
        self._action = action
        self._attr_name = action.capitalize()
        self._attr_unique_id = f"datakom_{node_id}_{device_id}_control_{action}"
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
            "identifiers": {(DOMAIN, str(self._device_id))},
            "name": self._device_name,
            "manufacturer": "Datakom",
            "model": "Device",
        }

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "device_id": self._device_id,
            "node_id": self._node_id,
            "device_name": self._device_name,
            "action": self._action,
            "description": f"Send {self._action} command to the device",
        }

    async def async_press(self) -> None:
        """Обработка нажатия кнопки управления."""
        url = f"{self._api_url}/device/control"
        payload = {
            "did": int(self._device_id),
            "action": self._action
        }
        _LOGGER.info(f"Datakom: Sending control command {self._action} to {url}")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=payload, timeout=30) as resp:
                    text = await resp.text()
                    _LOGGER.debug(f"Datakom: control response: {text}")
                    data = await resp.json()
                    
                    if data.get("success"):
                        _LOGGER.info(f"Datakom: Control command {self._action} successful")
                    else:
                        _LOGGER.error(f"Datakom: Control command {self._action} failed, response: {data}")
            except Exception as e:
                _LOGGER.error(f"Datakom: Control button {self._attr_unique_id} request error: {e}")
