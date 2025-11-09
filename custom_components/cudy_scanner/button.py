"""Button platform for Cudy Scanner."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CudyScannerCoordinator

BUTTON_TYPES: tuple[ButtonEntityDescription, ...] = (
    ButtonEntityDescription(
        key="reboot",
        name="Reboot",
        icon="mdi:restart",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Cudy Scanner buttons from a config entry."""
    coordinator: CudyScannerCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = [
        CudyScannerButton(coordinator, description, entry)
        for description in BUTTON_TYPES
    ]

    async_add_entities(entities)


class CudyScannerButton(CoordinatorEntity, ButtonEntity):
    """Representation of a Cudy Scanner button."""

    def __init__(
        self,
        coordinator: CudyScannerCoordinator,
        description: ButtonEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id)},
            name=entry.title,
            manufacturer="Cudy",
            model=coordinator.data.get("model") if coordinator.data else None,
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        if self.entity_description.key == "reboot":
            await self.coordinator.async_reboot()

