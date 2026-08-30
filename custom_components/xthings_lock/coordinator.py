"""Poll Xthings cloud for lock metadata."""
from __future__ import annotations

from datetime import timedelta
from typing import Any

from aiohttp import ClientSession
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import XthingsApiError, XthingsAuthError, XthingsClient
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

import logging

_LOGGER = logging.getLogger(__name__)


class XthingsCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    def __init__(self, hass: HomeAssistant, session: ClientSession, email: str, password: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = XthingsClient(email, password, session)

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        try:
            devices = await self.client.async_get_devices()
        except XthingsAuthError as err:
            raise UpdateFailed(f"Xthings login failed: {err}") from err
        except XthingsApiError as err:
            raise UpdateFailed(str(err)) from err
        out: dict[str, dict[str, Any]] = {}
        for dev in devices:
            uuid = (dev.get("uuid") or "").upper()
            if uuid:
                out[uuid] = dev
        return out
