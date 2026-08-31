"""Poll Xthings cloud for lock metadata; apply OpenAPI push when it arrives."""
from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from aiohttp import ClientSession
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import XthingsApiError, XthingsAuthError, XthingsClient, openapi_command
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, OPTIMISTIC_SECONDS

_LOGGER = logging.getLogger(__name__)


def _tz_hours(hass: HomeAssistant) -> str:
    """UTC offset hours for the Xthings app login payload."""
    try:
        tz = ZoneInfo(hass.config.time_zone or "UTC")
        offset = datetime.now(tz).utcoffset()
        if offset is None:
            return "0"
        return str(int(offset.total_seconds() // 3600))
    except Exception:  # noqa: BLE001
        return "0"


def _lock_value_from_state(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    text = str(value).strip().lower()
    if text in {"locked", "lock", "2"}:
        return 2
    if text in {"unlocked", "unlock", "1"}:
        return 1
    if text in {"jammed", "3"}:
        return 3
    return None


class XthingsCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    def __init__(
        self,
        hass: HomeAssistant,
        session: ClientSession,
        email: str,
        password: str,
        oauth_session: Any | None = None,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = XthingsClient(
            email, password, session, timezone_offset=_tz_hours(hass)
        )
        self._session = session
        self.oauth_session = oauth_session
        self._optimistic: dict[str, tuple[int, float]] = {}

    @property
    def can_command(self) -> bool:
        return self.oauth_session is not None

    def set_optimistic(self, uuid: str, locked: bool) -> None:
        value = 2 if locked else 1
        self._optimistic[uuid] = (value, time.monotonic())
        if uuid in self.data:
            params = dict(self.data[uuid].get("params") or {})
            params["is_locked"] = value
            self.data[uuid] = {**self.data[uuid], "params": params}
            self.async_set_updated_data(self.data)

    async def async_command(self, device_id: str, command: str) -> None:
        if not self.oauth_session:
            raise XthingsApiError("OpenAPI OAuth is not linked yet")
        await self.oauth_session.async_ensure_token_valid()
        token = self.oauth_session.token["access_token"]
        await openapi_command(self._session, token, device_id, command)

    def apply_push(self, payload: Any) -> None:
        """Merge Uhome.Notification DeviceState into coordinator data."""
        if not payload:
            return
        if isinstance(payload, list):
            for item in payload:
                self.apply_push(item)
            return
        if not isinstance(payload, dict):
            return
        body = payload.get("payload") if "payload" in payload else payload
        devices = []
        if isinstance(body, dict):
            devices = body.get("devices") or []
        elif isinstance(body, list):
            devices = body
        changed = False
        now = time.monotonic()
        for dev in devices:
            if not isinstance(dev, dict):
                continue
            uuid = str(dev.get("id") or dev.get("uuid") or "").upper()
            if not uuid:
                continue
            current = dict(self.data.get(uuid) or {"uuid": uuid, "params": {}, "wifi": {}})
            params = dict(current.get("params") or {})
            states = dev.get("states") or dev.get("state") or []
            items = []
            if isinstance(states, list):
                items = states
            elif isinstance(states, dict):
                items = [states]
            for item in items:
                if not isinstance(item, dict):
                    continue
                name = (item.get("name") or "").lower()
                cap = (item.get("capability") or "").lower()
                value = item.get("value")
                if name in {"lockstate", "lock_state"} or "lock" in cap and name in {"lockstate", "state"}:
                    mapped = _lock_value_from_state(value)
                    if mapped is not None:
                        params["is_locked"] = mapped
                        self._optimistic.pop(uuid, None)
                        changed = True
                if name in {"level", "battery"} and "battery" in cap:
                    try:
                        params["battery"] = int(value)
                        changed = True
                    except (TypeError, ValueError):
                        pass
            current["params"] = params
            self.data[uuid] = current
        # drop stale optimistic
        for uuid, (_val, ts) in list(self._optimistic.items()):
            if now - ts > OPTIMISTIC_SECONDS:
                self._optimistic.pop(uuid, None)
        if changed:
            self.async_set_updated_data(self.data)

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        try:
            devices = await self.client.async_get_devices()
        except XthingsAuthError as err:
            raise UpdateFailed(f"Xthings login failed: {err}") from err
        except XthingsApiError as err:
            raise UpdateFailed(str(err)) from err
        out: dict[str, dict[str, Any]] = {}
        now = time.monotonic()
        for dev in devices:
            uuid = (dev.get("uuid") or "").upper()
            if not uuid:
                continue
            opt = self._optimistic.get(uuid)
            if opt and now - opt[1] < OPTIMISTIC_SECONDS:
                params = dict(dev.get("params") or {})
                params["is_locked"] = opt[0]
                dev = {**dev, "params": params}
            else:
                self._optimistic.pop(uuid, None)
            out[uuid] = dev
        return out
