"""Diagnostics support for Cudy Scanner."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

TO_REDACT = {
    "password",
    "sysauth",
    "token",
    "_csrf",
    "csrf",
    "session_id",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = hass.data[DOMAIN].get(entry.entry_id, {})
    coordinator = data.get("coordinator")
    client = data.get("client")

    diagnostics_data: dict[str, Any] = {
        "entry": {
            "title": entry.title,
            "data": async_redact_data(entry.data, TO_REDACT),
            "options": entry.options,
        },
    }

    if coordinator:
        diagnostics_data["coordinator"] = {
            "data": coordinator.data,
            "last_update_success": coordinator.last_update_success,
            "last_exception": str(coordinator.last_exception) if coordinator.last_exception else None,
        }

    if client:
        diagnostics_data["client"] = {
            "host": client.host,
            "platform": client.platform,
            "has_session": bool(client.session_id),
        }

    return async_redact_data(diagnostics_data, TO_REDACT)
