"""Користувацькі виходи контролера (User outputs 1-16) - перемикачі.

Контролер приймає команду «увімкнути / вимкнути вихід N» (регістр 8201) - це функція виходу
«Remote Control Out N». Якщо її призначено реле контролера, перемикач показує справжній стан цього реле
(/device/io); інакше - останню надіслану команду (assumed state, відновлюється після перезапуску HA).
Які виходи показувати - налаштування інтеграції «Користувацькі виходи» (наприклад 1,3)."""
from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import DOMAIN, USER_OUTPUT_SIGNAL, parse_user_outputs
from .outputs import remote_control_outputs
from .control_api import async_send_control

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    control_key = entry.data.get("control_key", "")
    outputs = parse_user_outputs(entry.data.get("user_outputs"))
    if not control_key or not outputs:
        return
    runtime = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        DatakomUserOutputSwitch(
            entry.data.get("api_url", ""), entry.data.get("device_name", "Datakom Device"), number,
            control_key, runtime["coordinator"], runtime.get("command"),
        )
        for number in outputs
    )


class DatakomUserOutputSwitch(SwitchEntity, RestoreEntity):
    """Користувацький вихід N контролера."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:electric-switch"

    def __init__(self, api_url, device_name, number, control_key, coordinator, tracker=None):
        self._api_url = api_url
        self._device_name = device_name
        self._number = number
        self._control_key = control_key
        self._coordinator = coordinator
        self._tracker = tracker
        self.entity_id = f"switch.datakom_device_user_output_{number}"
        self._attr_unique_id = f"datakom_user_output_{number}"
        self._attr_translation_key = "user_output"
        self._attr_translation_placeholders = {"number": str(number)}
        self._attr_is_on = None

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "datakom_device")},
            "name": self._device_name,
            "manufacturer": "Datakom",
            "model": "Device",
        }

    @property
    def _relays(self) -> list[dict]:
        """Реле з функцією «Remote Control Out N» і відомим станом."""
        return [o for o in remote_control_outputs(self._coordinator.data, self._number) if "state" in o]

    @property
    def assumed_state(self) -> bool:
        return not self._relays

    @property
    def is_on(self) -> bool | None:
        relays = self._relays
        if relays:
            return any(o["state"] for o in relays)
        return self._attr_is_on

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "output": self._number,
            "relays": [o["output"] for o in remote_control_outputs(self._coordinator.data, self._number)],
        }

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state in ("on", "off"):
            self._attr_is_on = last.state == "on"
        self.async_on_remove(async_dispatcher_connect(self.hass, USER_OUTPUT_SIGNAL, self._on_switched))
        # Справжній стан реле приходить з оновленням даних
        self.async_on_remove(self._coordinator.async_add_listener(self.async_write_ha_state))

    @callback
    def _on_switched(self, number: int, on: bool) -> None:
        """Вихід перемкнуто сервісом ha_datakom.set_user_output."""
        if number == self._number:
            self._attr_is_on = on
            self.async_write_ha_state()

    async def _switch(self, on: bool) -> None:
        state = "on" if on else "off"
        await async_send_control(
            self.hass, self._api_url, self._control_key,
            {"action": "output", "output": self._number, "state": state},
            self._coordinator, self._tracker, label=f"output {self._number} {state}",
        )
        async_dispatcher_send(self.hass, USER_OUTPUT_SIGNAL, self._number, on)

    async def async_turn_on(self, **kwargs) -> None:
        await self._switch(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._switch(False)
