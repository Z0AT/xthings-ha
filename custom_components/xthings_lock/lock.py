from __future__ import annotations

from typing import Any

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LOCKED_VALUES, UNLOCKED_VALUES
from .coordinator import XthingsCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: XthingsCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        XthingsLock(coordinator, uuid) for uuid in coordinator.data
    )


class XthingsLock(CoordinatorEntity[XthingsCoordinator], LockEntity):
    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = 0

    def __init__(self, coordinator: XthingsCoordinator, uuid: str) -> None:
        super().__init__(coordinator)
        self._uuid = uuid
        self._attr_unique_id = f"{uuid}_lock"
        dev = coordinator.data[uuid]
        self._attr_device_info = {
            "identifiers": {(DOMAIN, uuid)},
            "name": dev.get("name") or uuid,
            "manufacturer": "Xthings / ULTRALOQ",
            "model": dev.get("model") or "Bolt",
            "sw_version": str((dev.get("params") or {}).get("version") or ""),
        }

    def _dev(self) -> dict[str, Any]:
        return self.coordinator.data.get(self._uuid) or {}

    @property
    def is_locked(self) -> bool | None:
        params = self._dev().get("params") or {}
        val = params.get("is_locked")
        if val in LOCKED_VALUES:
            return True
        if val in UNLOCKED_VALUES:
            return False
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        wifi = self._dev().get("wifi") or {}
        params = self._dev().get("params") or {}
        return {
            "wifi_ssid": wifi.get("wifi_ssid") or params.get("wifi_ssid"),
            "wifi_remote": wifi.get("wifi_remote") or params.get("wifi_remote"),
            "wifi_strength": wifi.get("wifi_strength") or params.get("wifi_strength"),
            "is_locked_raw": params.get("is_locked"),
        }

    async def async_lock(self, **kwargs: Any) -> None:
        raise HomeAssistantError(
            "Wi-Fi lock/unlock is MQTT to AWS IoT (app client cert), not HTTP. "
            "Use the Xthings app or BLE until MQTT is wired."
        )

    async def async_unlock(self, **kwargs: Any) -> None:
        await self.async_lock()
