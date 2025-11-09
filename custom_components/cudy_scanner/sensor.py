"""Sensor platform for Cudy Scanner."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CudyScannerCoordinator

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="firmware_version",
        name="Firmware Version",
        icon="mdi:chip",
    ),
    SensorEntityDescription(
        key="wan_ip",
        name="WAN IP",
        icon="mdi:ip-network",
    ),
    SensorEntityDescription(
        key="uptime",
        name="Uptime",
        icon="mdi:clock-outline",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Cudy Scanner sensors from a config entry."""
    coordinator: CudyScannerCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = [
        CudyScannerSensor(coordinator, description, entry)
        for description in SENSOR_TYPES
    ]

    async_add_entities(entities)


class CudyScannerSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Cudy Scanner sensor."""

    def __init__(
        self,
        coordinator: CudyScannerCoordinator,
        description: SensorEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id)},
            name=entry.title,
            manufacturer="Cudy",
            model=coordinator.data.get("model") if coordinator.data else None,
            sw_version=coordinator.data.get("firmware_version")
            if coordinator.data
            else None,
        )

    @property
    def native_value(self) -> str | int | None:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
        
        value = self.coordinator.data.get(self.entity_description.key)
        
        # For uptime, return seconds if available for proper duration formatting
        if self.entity_description.key == "uptime":
            uptime_seconds = self.coordinator.data.get("uptime_seconds")
            if uptime_seconds is not None:
                return uptime_seconds
            # Fallback to string if seconds not available
            return value
        
        return value
    
    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        if self.entity_description.key == "uptime":
            return "s"  # seconds
        return None

