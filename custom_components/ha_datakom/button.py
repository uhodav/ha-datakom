"""Платформа button для Datakom интеграции (REST API)."""
import asyncio
import logging
import aiohttp

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.event import async_call_later
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Дії, дозволені API за замовчуванням (genset/mains - перемикання навантаження - вимкнені)
CONTROL_ACTIONS = ["stop", "auto", "manual", "test"]

# Сервер відповідає за ~20 с (команда в черзі) або ~10 с (підтвердження), але запити виконуються по одному:
# кілька натискань поспіль чекають одне одного
CONTROL_TIMEOUT = 90


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
    """Button для управления устройством Datakom (Run/Auto/Manual/Test/Stop)."""

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
        """Обработка нажатия кнопки управления.

        Контроллер подключается к API примерно раз в минуту: команда между подключениями стоит в очереди
        сервера (он отвечает «queued» через ~20 с). Ход команды - в sensor.datakom_device_control_command."""
        tracker = self._tracker
        # Та же команда уже отправляется или ждёт в очереди - повторное нажатие ничего не меняет
        if tracker and tracker.action == self._action and tracker.state in ("sending", "queued"):
            _LOGGER.info(f"Datakom: Control command {self._action} already {tracker.state}, press ignored")
            return

        request_id = tracker.start(self._action, self._coordinator.data) if tracker else 0
        url = f"{self._api_url}/device/control"
        _LOGGER.info(f"Datakom: Sending control command {self._action} to {url}")
        try:
            session = async_get_clientsession(self.hass)
            async with session.post(
                url,
                json={"action": self._action},
                headers={"X-API-Key": self._control_key},
                timeout=aiohttp.ClientTimeout(total=CONTROL_TIMEOUT),
            ) as resp:
                data = await resp.json(content_type=None)
        except Exception as e:
            reason = (
                f"немає відповіді від API-сервера за {CONTROL_TIMEOUT} с"
                if isinstance(e, (asyncio.TimeoutError, TimeoutError))
                else (str(e) or type(e).__name__)
            )
            _LOGGER.error(f"Datakom: Control button {self._attr_unique_id} request error: {reason}")
            if tracker:
                tracker.finish(request_id, "failed", reason)
            raise HomeAssistantError(f"Datakom: команда {self._action} не відправлена: {reason}") from e

        if not data.get("success"):
            error = data.get("error") or "невідома помилка"
            _LOGGER.error(f"Datakom: Control command {self._action} failed, response: {data}")
            if tracker:
                tracker.finish(request_id, "failed", error)
            raise HomeAssistantError(f"Datakom: команда {self._action} не виконана: {error}")
        if data.get("queued"):
            _LOGGER.info(f"Datakom: Control command {self._action} queued until the controller reconnects")
            if tracker:
                tracker.finish(request_id, "queued")
        else:
            _LOGGER.info(f"Datakom: Control command {self._action} confirmed by controller")
            if tracker:
                tracker.finish(request_id, "confirmed")
        # Контроллер присылает новый режим через несколько секунд после подтверждения
        async def _refresh(_now):
            await self._coordinator.async_request_refresh()

        for delay in (3, 10):
            async_call_later(self.hass, delay, _refresh)
