"""Xthings / U-tec cloud client (app login, not OpenAPI)."""
from __future__ import annotations

import json
import secrets
import string
import time
from typing import Any

from aiohttp import ClientSession

from uuid import uuid4

from .const import (
    ADDRESS_URL,
    APP_ID,
    CLIENT_ID,
    DEVICE_GET_URL,
    DEVICE_LIST_URL,
    LOGIN_URL,
    OPENAPI_ACTION,
    ROOM_URL,
    TOKEN_URL,
    USER_AGENT,
)


class XthingsAuthError(Exception):
    """Login failed."""


class XthingsApiError(Exception):
    """Unexpected cloud response."""


class XthingsClient:
    def __init__(
        self,
        email: str,
        password: str,
        session: ClientSession,
        timezone_offset: str = "0",
    ) -> None:
        self._email = email
        self._password = password
        self._session = session
        self._timezone = timezone_offset
        self._token: str | None = None
        self._mobile_uuid = "".join(
            secrets.choice(string.ascii_uppercase + string.digits) for _ in range(32)
        )

    def _headers(self) -> dict[str, str]:
        return {
            "accept": "*/*",
            "content-type": "application/x-www-form-urlencoded",
            "user-agent": USER_AGENT,
        }

    async def _post(self, url: str, data: dict[str, str]) -> dict[str, Any]:
        async with self._session.post(url, headers=self._headers(), data=data, timeout=60) as resp:
            resp.raise_for_status()
            return await resp.json(content_type=None)

    @staticmethod
    def _ok(resp: dict[str, Any], msg: str) -> dict[str, Any]:
        if not isinstance(resp, dict) or not resp:
            raise XthingsApiError(msg)
        err = resp.get("error")
        if isinstance(err, str) and err.strip():
            raise XthingsApiError(err)
        if err not in (None, False, 0, "0", ""):
            if isinstance(err, dict):
                raise XthingsApiError(msg)
            raise XthingsApiError(str(err))
        code = resp.get("code")
        if code is not None and str(code) not in {"0", "200"}:
            raise XthingsApiError(resp.get("description") or msg)
        return resp

    async def login(self) -> None:
        tok = self._ok(
            await self._post(
                TOKEN_URL,
                {
                    "appid": APP_ID,
                    "clientid": CLIENT_ID,
                    "timezone": self._timezone,
                    "uuid": self._mobile_uuid,
                    "version": "V3.2",
                },
            ),
            "token",
        )
        token = (tok.get("data") or {}).get("token")
        if not token:
            raise XthingsApiError("token missing")
        self._token = token
        try:
            self._ok(
                await self._post(
                    LOGIN_URL,
                    {
                        "data": json.dumps(
                            {
                                "email": self._email,
                                "timestamp": str(time.time()),
                                "password": self._password,
                            }
                        ),
                        "token": self._token,
                    },
                ),
                "login",
            )
        except XthingsApiError as err:
            raise XthingsAuthError(str(err)) from err

    async def async_get_devices(self) -> list[dict[str, Any]]:
        if not self._token:
            await self.login()
        try:
            return await self._fetch_devices()
        except XthingsApiError:
            self._token = None
            await self.login()
            return await self._fetch_devices()

    async def _fetch_devices(self) -> list[dict[str, Any]]:
        assert self._token
        ts = str(time.time())
        addr = self._ok(
            await self._post(ADDRESS_URL, {"data": json.dumps({"timestamp": ts}), "token": self._token}),
            "address",
        )
        rooms: list[dict[str, Any]] = []
        for address in addr.get("data") or []:
            room_resp = self._ok(
                await self._post(
                    ROOM_URL,
                    {
                        "data": json.dumps({"id": address["id"], "timestamp": str(time.time())}),
                        "token": self._token,
                    },
                ),
                "room",
            )
            rooms.extend(room_resp.get("data") or [])
        devices: list[dict[str, Any]] = []
        for room in rooms:
            listed = self._ok(
                await self._post(
                    DEVICE_LIST_URL,
                    {
                        "data": json.dumps({"room_id": room["id"], "timestamp": str(time.time())}),
                        "token": self._token,
                    },
                ),
                "device list",
            )
            for dev in listed.get("data") or []:
                detail = self._ok(
                    await self._post(
                        DEVICE_GET_URL,
                        {
                            "data": json.dumps({"uuid": dev.get("uuid"), "timestamp": str(time.time())}),
                            "token": self._token,
                        },
                    ),
                    "device get",
                )
                merged = dict(dev)
                if isinstance(detail.get("data"), dict):
                    merged.update(detail["data"])
                merged["room_name"] = room.get("name") or ""
                # never keep wifi password in coordinator state
                params = dict(merged.get("params") or {})
                params.pop("wifi_password", None)
                merged["params"] = params
                wifi = dict(merged.get("wifi") or {})
                wifi.pop("password", None)
                wifi.pop("wifi_password", None)
                merged["wifi"] = wifi
                if "user" in merged:
                    merged["user"] = {"uid": (merged.get("user") or {}).get("uid")}
                devices.append(merged)
        return devices


async def openapi_command(
    session: ClientSession,
    access_token: str,
    device_id: str,
    command: str,
) -> dict[str, Any]:
    """Send st.lock lock/unlock via official OpenAPI (cloud → lock Wi-Fi)."""
    payload = {
        "header": {
            "namespace": "Uhome.Device",
            "name": "Command",
            "messageId": str(uuid4()),
            "payloadVersion": "1",
        },
        "payload": {
            "devices": [
                {
                    "id": device_id,
                    "command": {"capability": "st.lock", "name": command},
                }
            ]
        },
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {access_token}",
        "user-agent": USER_AGENT,
    }
    async with session.post(OPENAPI_ACTION, json=payload, headers=headers, timeout=60) as resp:
        data = await resp.json(content_type=None)
        if resp.status >= 400:
            raise XthingsApiError(f"OpenAPI HTTP {resp.status}")
        err = (data.get("payload") or {}).get("error") if isinstance(data, dict) else None
        if err:
            raise XthingsApiError(err.get("message") or str(err))
        return data if isinstance(data, dict) else {}


async def openapi_configure_notification(
    session: ClientSession,
    access_token: str,
    url: str,
    push_secret: str,
) -> dict[str, Any]:
    """Tell Xthings cloud to POST DeviceState events to HA."""
    payload = {
        "header": {
            "namespace": "Uhome.Configure",
            "name": "Set",
            "messageId": str(uuid4()),
            "payloadVersion": "1",
        },
        "payload": {
            "configure": {
                "notification": {
                    "access_token": push_secret,
                    "url": url,
                }
            }
        },
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {access_token}",
        "user-agent": USER_AGENT,
    }
    async with session.post(OPENAPI_ACTION, json=payload, headers=headers, timeout=60) as resp:
        data = await resp.json(content_type=None)
        if resp.status >= 400:
            raise XthingsApiError(f"OpenAPI notify HTTP {resp.status}")
        err = (data.get("payload") or {}).get("error") if isinstance(data, dict) else None
        if err:
            raise XthingsApiError(err.get("message") or str(err))
        return data if isinstance(data, dict) else {}
