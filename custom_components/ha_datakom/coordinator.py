"""Общий опрос Datakom API для всех сущностей устройства."""
import asyncio
import logging
from datetime import timedelta

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=15)


class DatakomCoordinator(DataUpdateCoordinator):
    """Читает /dump_devm, /dump_devm_alarm и /health одним циклом опроса."""

    def __init__(self, hass: HomeAssistant, api_url: str, language: str, update_interval_min: int):
        super().__init__(
            hass,
            _LOGGER,
            name="Datakom",
            update_interval=timedelta(minutes=update_interval_min),
        )
        self.api_url = api_url
        self.language = language
        self._session = async_get_clientsession(hass)

    async def _get_json(self, path: str) -> dict:
        async with self._session.get(f"{self.api_url}/{path}", timeout=REQUEST_TIMEOUT) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise UpdateFailed(f"{path}: HTTP {resp.status}: {text[:200]}")
            return await resp.json(content_type=None)

    async def _async_update_data(self) -> dict:
        dump, alarm, health = await asyncio.gather(
            self._get_json(f"dump_devm?language={self.language}"),
            self._get_json(f"dump_devm_alarm?language={self.language}"),
            self._get_json("health"),
            return_exceptions=True,
        )

        if isinstance(dump, Exception):
            raise UpdateFailed(f"Datakom dump_devm failed: {dump}") from dump
        if not dump.get("success"):
            raise UpdateFailed(f"Datakom dump_devm error: {dump.get('error')}")

        if isinstance(alarm, Exception) or not alarm.get("success"):
            _LOGGER.warning(f"Datakom: dump_devm_alarm failed: {alarm}")
            alarm = None
        if isinstance(health, Exception):
            _LOGGER.warning(f"Datakom: health failed: {health}")
            health = None

        return {
            "params": {str(p["id"]): p for p in dump.get("result", [])},
            "alarm": alarm,
            "health": health,
            "stale": bool(dump.get("stale", False)),
            "data_age_seconds": dump.get("data_age_seconds"),
            "timestamp": dump.get("timestamp"),
        }
