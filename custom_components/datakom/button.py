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
