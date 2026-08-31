from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import SIGNAL_STRENGTH_DECIBELS_MILLIWATT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import BATTERY_LEVEL, DOMAIN
from .coordinator import XthingsCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: XthingsCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    ents: list = []
    for uuid in coordinator.data:
        ents.append(XthingsBattery(coordinator, uuid))
        ents.append(XthingsWifiRssi(coordinator, uuid))
    async_add_entities(ents)


class _Base(CoordinatorEntity[XthingsCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: XthingsCoordinator, uuid: str) -> None:
        super().__init__(coordinator)
        self._uuid = uuid
        dev = coordinator.data[uuid]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, uuid)},
            name=dev.get("name") or uuid,
            manufacturer="U-tec",
            model=dev.get("model") or "ULTRALOQ Bolt",
        )

    def _params(self) -> dict:
        return (self.coordinator.data.get(self._uuid) or {}).get("params") or {}

    def _wifi(self) -> dict:
        return (self.coordinator.data.get(self._uuid) or {}).get("wifi") or {}


class XthingsBattery(_Base):
    _attr_name = "Battery"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = list(BATTERY_LEVEL.values())

    def __init__(self, coordinator: XthingsCoordinator, uuid: str) -> None:
        super().__init__(coordinator, uuid)
        self._attr_unique_id = f"{uuid}_battery"

    @property
    def native_value(self) -> str | None:
        raw = self._params().get("battery")
        if raw is None:
            return None
        return BATTERY_LEVEL.get(int(raw), str(raw))


class XthingsWifiRssi(_Base):
    _attr_name = "Wi-Fi RSSI"
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: XthingsCoordinator, uuid: str) -> None:
        super().__init__(coordinator, uuid)
        self._attr_unique_id = f"{uuid}_wifi_rssi"

    @property
    def native_value(self) -> int | None:
        val = self._wifi().get("wifi_strength")
        if val is None:
            val = self._params().get("wifi_strength")
        return int(val) if val is not None else None
