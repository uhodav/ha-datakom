"""Состояние последней команды керування контролером (кнопки Stop/Auto/Manual/Test).

Контролер не тримає постійного зʼєднання з API-сервером: він підключається приблизно раз на хвилину.
Команда, натиснута між підключеннями, стоїть у черзі сервера і виконується при наступному підключенні,
тому між натисканням і зміною режиму минає до ~1,5 хв. Трекер показує цей шлях:
idle -> sending -> queued | confirmed -> done, або failed / expired.
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant, callback
from homeassistant.util import dt as dt_util

# Стани, у яких команда ще виконується (картка підсвічує кнопку)
ACTIVE_STATES = ("sending", "queued", "confirmed")
COMMAND_STATES = ["idle", "sending", "queued", "confirmed", "done", "failed", "expired"]

# Скільки команда живе в черзі сервера (DATAKOM_CONTROL_QUEUE_SECONDS, типово 120 с) + запас
QUEUE_LIFETIME = timedelta(seconds=130)
# Скільки чекати зміни режиму після підтвердження контролером
CONFIRM_LIFETIME = timedelta(seconds=120)

# Режим контролера (параметр 103), у який переводить кожна кнопка
MODE_BY_ACTION = {"stop": "stop", "auto": "auto", "manual": "manual", "test": "test"}
GENSET_MODE_BY_VALUE = {"1": "stop", "2": "manual", "4": "auto", "8": "test"}


class CommandTracker:
    """Останнє натискання кнопки керування і його доля."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.state = "idle"
        self.action: str | None = None
        self.requested_at: datetime | None = None
        self.updated_at: datetime | None = None
        self.expires_at: datetime | None = None
        self.error: str | None = None
        self.mode_before: str | None = None
        self._telemetry_at = None  # мітка телеметрії на момент постановки в чергу
        self._request_id = 0
        self._listeners: list[Callable[[], None]] = []

    @property
    def active(self) -> bool:
        return self.state in ACTIVE_STATES

    @property
    def attributes(self) -> dict:
        iso = lambda d: d.isoformat() if d else None
        return {
            "action": self.action,
            "requested_at": iso(self.requested_at),
            "updated_at": iso(self.updated_at),
            "expires_at": iso(self.expires_at),
            "error": self.error,
        }

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    @callback
    def _notify(self) -> None:
        for listener in list(self._listeners):
            listener()

    @staticmethod
    def mode_from(data: dict | None) -> str | None:
        param = ((data or {}).get("params") or {}).get("103") or {}
        return GENSET_MODE_BY_VALUE.get(str(param.get("value")))

    @callback
    def start(self, action: str, data: dict | None = None) -> int:
        """Нове натискання: повертає id запиту (відповідь застарілого запиту не перезапише новіший)."""
        self._request_id += 1
        self.mode_before = self.mode_from(data)
        now = dt_util.utcnow()
        self.state, self.action, self.error, self.expires_at = "sending", action, None, None
        self.requested_at = self.updated_at = now
        self._notify()
        return self._request_id

    @property
    def _already_in_mode(self) -> bool:
        """Контролер уже був у режимі цієї кнопки: зміни режиму не буде, чекати її не можна."""
        return self.mode_before is not None and self.mode_before == MODE_BY_ACTION.get(self.action)

    @callback
    def finish(self, request_id: int, state: str, error: str | None = None, data: dict | None = None) -> None:
        if request_id != self._request_id:
            return
        now = dt_util.utcnow()
        # Підтверджена контролером, а режим уже потрібний - виконано одразу
        if state == "confirmed" and self._already_in_mode:
            state = "done"
        self.state, self.error, self.updated_at = state, error, now
        self._telemetry_at = (data or {}).get("timestamp")
        if state == "queued":
            self.expires_at = now + QUEUE_LIFETIME
        elif state == "confirmed":
            self.expires_at = now + CONFIRM_LIFETIME
        else:
            self.expires_at = None
        self._notify()

    @callback
    def check(self, data: dict | None) -> None:
        """Викликається після кожного оновлення даних: режим змінився -> done, час вийшов -> expired."""
        if self.state not in ("queued", "confirmed"):
            return
        mode = self.mode_from(data)
        target = MODE_BY_ACTION.get(self.action)
        now = dt_util.utcnow()
        # Виконано, коли режим змінився на потрібний (якщо вже був таким - чекаємо підтвердження/таймауту)
        fresh = not (data or {}).get("stale")
        if mode and mode == target and mode != self.mode_before and fresh:
            self.state, self.updated_at, self.expires_at = "done", now, None
        elif (
            self.state == "queued" and self._already_in_mode and fresh
            and (data or {}).get("timestamp") not in (None, self._telemetry_at)
        ):
            # Режим уже потрібний: нова телеметрія означає, що контролер підключився,
            # а сервер надсилає команду з черги одразу після пакета - виконано
            self.state, self.updated_at, self.expires_at = "done", now, None
        elif self.expires_at and now > self.expires_at:
            # Підтверджена контролером або режим уже потрібний - виконана; інакше черга минула
            self.state = "done" if (self.state == "confirmed" or mode == target) else "expired"
            self.updated_at, self.expires_at = now, None
            if self.state == "expired":
                self.error = "Контролер не підключився, поки команда була в черзі"
        else:
            return
        self._notify()
