from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import XthingsCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: XthingsCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities(XthingsWifiRemote(coordinator, uuid) for uuid in coordinator.data)


class XthingsWifiRemote(CoordinatorEntity[XthingsCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Wi-Fi remote"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: XthingsCoordinator, uuid: str) -> None:
        super().__init__(coordinator)
        self._uuid = uuid
        self._attr_unique_id = f"{uuid}_wifi_remote"
        dev = coordinator.data[uuid]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, uuid)},
            name=dev.get("name") or uuid,
            manufacturer="U-tec",
            model=dev.get("model") or "ULTRALOQ Bolt",
        )

    @property
    def is_on(self) -> bool:
        dev = self.coordinator.data.get(self._uuid) or {}
        wifi = dev.get("wifi") or {}
        params = dev.get("params") or {}
        return int(wifi.get("wifi_remote") or params.get("wifi_remote") or 0) == 1
