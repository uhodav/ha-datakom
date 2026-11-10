"""Відправка команди керування на API-сервер (POST /device/control з X-API-Key).

Контролер підключається до API приблизно раз на хвилину: команда між підключеннями стоїть у черзі
сервера (він відповідає «queued» через ~20-30 с). Хід команди - у CommandTracker
(sensor.datakom_device_control_command)."""
from __future__ import annotations

import asyncio
import logging

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_call_later

_LOGGER = logging.getLogger(__name__)

# Сервер відповідає за ~20 с (команда в черзі) або ~10 с (підтвердження), але запити виконуються по одному:
# кілька натискань поспіль чекають одне одного
CONTROL_TIMEOUT = 90


async def async_send_control(hass: HomeAssistant, api_url: str, control_key: str, payload: dict,
                             coordinator, tracker=None, label: str | None = None) -> None:
    """Надіслати команду (payload = {"action": ...} [+ output/state]) і відстежити її в tracker."""
    action = payload["action"]
    label = label or action
    request_id = tracker.start(action, coordinator.data) if tracker else 0
    url = f"{api_url}/device/control"
    _LOGGER.info(f"Datakom: Sending control command {label} to {url}")
    try:
        session = async_get_clientsession(hass)
        async with session.post(
            url,
            json=payload,
            headers={"X-API-Key": control_key},
            timeout=aiohttp.ClientTimeout(total=CONTROL_TIMEOUT),
        ) as resp:
            data = await resp.json(content_type=None)
    except Exception as e:
        reason = (
            f"немає відповіді від API-сервера за {CONTROL_TIMEOUT} с"
            if isinstance(e, (asyncio.TimeoutError, TimeoutError))
            else (str(e) or type(e).__name__)
        )
        _LOGGER.error(f"Datakom: Control command {label} request error: {reason}")
        if tracker:
            tracker.finish(request_id, "failed", reason)
        raise HomeAssistantError(f"Datakom: команда {label} не відправлена: {reason}") from e

    if not data.get("success"):
        error = data.get("error") or "невідома помилка"
        _LOGGER.error(f"Datakom: Control command {label} failed, response: {data}")
        if tracker:
            tracker.finish(request_id, "failed", error)
        raise HomeAssistantError(f"Datakom: команда {label} не виконана: {error}")
    if data.get("queued"):
        _LOGGER.info(f"Datakom: Control command {label} queued until the controller reconnects")
        if tracker:
            tracker.finish(request_id, "queued", data=coordinator.data)
    else:
        _LOGGER.info(f"Datakom: Control command {label} confirmed by controller")
        if tracker:
            tracker.finish(request_id, "confirmed", data=coordinator.data)

    # Контролер присылает новый режим через несколько секунд после подтверждения
    async def _refresh(_now):
        await coordinator.async_request_refresh()

    for delay in (3, 10):
        async_call_later(hass, delay, _refresh)


async def async_post_api(hass: HomeAssistant, api_url: str, control_key: str, path: str, payload: dict,
                         timeout: int = 150) -> dict:
    """POST на API-сервер з X-API-Key; помилка -> HomeAssistantError з текстом сервера."""
    try:
        session = async_get_clientsession(hass)
        async with session.post(
            f"{api_url}/{path}", json=payload, headers={"X-API-Key": control_key},
            timeout=aiohttp.ClientTimeout(total=timeout),
        ) as resp:
            data = await resp.json(content_type=None)
    except Exception as e:
        reason = (f"немає відповіді від API-сервера за {timeout} с"
                  if isinstance(e, (asyncio.TimeoutError, TimeoutError)) else (str(e) or type(e).__name__))
        raise HomeAssistantError(f"Datakom: {path}: {reason}") from e
    if not isinstance(data, dict) or not data.get("success"):
        error = (data or {}).get("error") if isinstance(data, dict) else str(data)
        raise HomeAssistantError(f"Datakom: {path}: {error or 'невідома помилка'}")
    return data
