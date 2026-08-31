from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import XthingsCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics with credentials and tokens stripped."""
    stored = hass.data.get(DOMAIN, {}).get(entry.entry_id) or {}
    coordinator: XthingsCoordinator | None = stored.get("coordinator")
    devices = []
    if coordinator and coordinator.data:
        for uuid, dev in coordinator.data.items():
            params = dev.get("params") or {}
            wifi = dev.get("wifi") or {}
            devices.append(
                {
                    "uuid": uuid,
                    "name": dev.get("name"),
                    "model": dev.get("model"),
                    "is_locked": params.get("is_locked"),
                    "battery": params.get("battery"),
                    "wifi_remote": wifi.get("wifi_remote") or params.get("wifi_remote"),
                    "wifi_ssid": wifi.get("wifi_ssid") or params.get("wifi_ssid"),
                    "wifi_strength": wifi.get("wifi_strength")
                    or params.get("wifi_strength"),
                }
            )
    return {
        "openapi_linked": bool(entry.data.get("token")),
        "webhook_registered": bool(stored.get("webhook_id")),
        "device_count": len(devices),
        "devices": devices,
    }
