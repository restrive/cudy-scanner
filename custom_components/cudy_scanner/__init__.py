"""The Cudy Scanner integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, UPDATE_INTERVAL_STATUS
from .coordinator import CudyScannerCoordinator
from .cudy_client import CudyClient

_LOGGER = logging.getLogger(__package__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]

SERVICE_REBOOT = "reboot"
SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): cv.string,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Cudy Scanner from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create client
    client = CudyClient(
        host=entry.data["host"],
        password=entry.data["password"],
        username=entry.data.get("username", ""),
        use_https=entry.data.get("use_https", False),
        verify_ssl=entry.data.get("verify_ssl", False),
    )

    # Create coordinator
    coordinator = CudyScannerCoordinator(
        hass, client, update_interval=UPDATE_INTERVAL_STATUS
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "client": client,
    }

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services (only once)
    if not hass.services.has_service(DOMAIN, SERVICE_REBOOT):
        async def async_reboot_service(service_call: ServiceCall) -> None:
            """Handle reboot service call."""
            device_id = service_call.data.get("device_id")
            
            # Find the entry by device_id
            entry_id = None
            for eid, data in hass.data.get(DOMAIN, {}).items():
                if data.get("coordinator"):
                    # Check if this entry matches the device
                    config_entry = hass.config_entries.async_get_entry(eid)
                    if config_entry and config_entry.unique_id == device_id:
                        entry_id = eid
                        break
            
            if not entry_id:
                raise HomeAssistantError(f"Device {device_id} not found")
            
            coordinator: CudyScannerCoordinator = hass.data[DOMAIN][entry_id]["coordinator"]
            result = await coordinator.async_reboot()
            
            if not result:
                raise HomeAssistantError("Reboot failed or cooldown active")

        hass.services.async_register(
            DOMAIN, SERVICE_REBOOT, async_reboot_service, schema=SERVICE_SCHEMA
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Cudy Scanner config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        # Close client session
        client: CudyClient = hass.data[DOMAIN][entry.entry_id]["client"]
        await client.close()

        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok
