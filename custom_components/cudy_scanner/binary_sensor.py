"""Binary sensor platform for Cudy Scanner."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CudyScannerCoordinator

BINARY_SENSOR_TYPES: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key="online",
        name="Online",
        icon="mdi:router-wireless",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Cudy Scanner binary sensors from a config entry."""
    coordinator: CudyScannerCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = [
        CudyScannerBinarySensor(coordinator, description, entry)
        for description in BINARY_SENSOR_TYPES
    ]

    async_add_entities(entities)


class CudyScannerBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Cudy Scanner binary sensor."""

    def __init__(
        self,
        coordinator: CudyScannerCoordinator,
        description: BinarySensorEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id)},
            name=entry.title,
            manufacturer="Cudy",
            model=coordinator.data.get("model") if coordinator.data else None,
        )

    @property
    def is_on(self) -> bool:
        """Return the state of the binary sensor."""
        # Online if we have data and no last update error
        return (
            self.coordinator.data is not None
            and self.coordinator.last_update_success
        )

