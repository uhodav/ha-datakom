"""Тижневий графік контролера (Rainbow Plus «Scheduler»): години, коли режим AUTO може запускати генератор.

Одне поле на день: проміжки «06:00-24:00» через кому (лише цілі години; порожньо - жодної години).
Читає /device/io (listener оновлює графік раз на 10 хв), записує POST /device/schedule: listener змінює
лише слова графіка в блоці конфігурації і перевіряє запис зворотним читанням. Потрібен ключ керування."""
from __future__ import annotations

import logging
import re

from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN
from .control_api import async_post_api

_LOGGER = logging.getLogger(__name__)

DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
_RANGE = re.compile(r"^(\d{1,2})(?::00)?\s*-\s*(\d{1,2})(?::00)?$")


def hours_to_text(hours: list[int]) -> str:
    """[6, 7, ..., 23] -> «06:00-24:00»; [0..5, 20..23] -> «00:00-06:00, 20:00-24:00»."""
    ranges, start, prev = [], None, None
    for h in sorted(set(hours)):
        if start is None:
            start = prev = h
        elif h == prev + 1:
            prev = h
        else:
            ranges.append((start, prev + 1))
            start = prev = h
    if start is not None:
        ranges.append((start, prev + 1))
    return ", ".join(f"{a:02d}:00-{b:02d}:00" for a, b in ranges)


def text_to_hours(text: str) -> list[int]:
    """«06-24», «06:00-12:00, 14:00-24:00», порожньо -> години; ValueError, якщо формат не той."""
    hours = set()
    for part in filter(None, (p.strip() for p in (text or "").replace(";", ",").split(","))):
        m = _RANGE.match(part)
        if not m:
            raise ValueError(part)
        a, b = int(m.group(1)), int(m.group(2))
        if not 0 <= a < b <= 24:
            raise ValueError(part)
        hours.update(range(a, b))
    return sorted(hours)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    control_key = entry.data.get("control_key", "")
    runtime = hass.data[DOMAIN][entry.entry_id]
    coordinator = runtime["coordinator"]
    # Графік є лише коли API-сервер віддає /device/io; змінювати його можна лише з ключем керування
    if not control_key or not ((coordinator.data or {}).get("io") or {}).get("schedule"):
        return
    async_add_entities(
        DatakomScheduleText(coordinator, entry.data.get("api_url", ""), control_key,
                            entry.data.get("device_name", "Datakom Device"), day)
        for day in DAYS
    )


class DatakomScheduleText(CoordinatorEntity, TextEntity):
    """Години роботи AUTO на один день тижня."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:calendar-clock"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_max = 255
    # Вимкнено за замовчуванням: увімкнути в налаштуваннях сутностей, щоб змінювати графік з HA
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator, api_url: str, control_key: str, device_name: str, day: str):
        super().__init__(coordinator)
        self._api_url = api_url
        self._control_key = control_key
        self._device_name = device_name
        self._day = day
        self.entity_id = f"text.datakom_device_schedule_{day}"
        self._attr_unique_id = f"datakom_schedule_{day}"
        self._attr_translation_key = f"schedule_{day}"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "datakom_device")},
            "name": self._device_name,
            "manufacturer": "Datakom",
            "model": "Device",
        }

    @property
    def _hours(self) -> list[int] | None:
        schedule = ((self.coordinator.data or {}).get("io") or {}).get("schedule") or {}
        return schedule.get(self._day)

    @property
    def available(self) -> bool:
        return self._hours is not None

    @property
    def native_value(self) -> str | None:
        hours = self._hours
        return None if hours is None else hours_to_text(hours)

    @property
    def extra_state_attributes(self) -> dict:
        io = (self.coordinator.data or {}).get("io") or {}
        return {"hours": self._hours, "updated": io.get("config_timestamp")}

    async def async_set_value(self, value: str) -> None:
        try:
            hours = text_to_hours(value)
        except ValueError as e:
            raise HomeAssistantError(
                f"Datakom: графік «{value}»: незрозумілий проміжок «{e}». Формат: 06:00-24:00, 00:00-05:00"
            ) from e
        if hours == self._hours:
            return
        _LOGGER.info(f"Datakom: writing scheduler {self._day} = {hours}")
        result = await async_post_api(
            self.hass, self._api_url, self._control_key, "device/schedule", {"schedule": {self._day: hours}}
        )
        # Записаний і перевірений графік - одразу в дані, не чекаючи наступного читання (раз на 10 хв)
        data = self.coordinator.data or {}
        io = {**(data.get("io") or {}), "schedule": result.get("schedule")}
        self.coordinator.async_set_updated_data({**data, "io": io})
