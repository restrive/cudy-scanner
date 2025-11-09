"""Config flow for Cudy Scanner integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_USE_HTTPS,
    CONF_VERIFY_SSL,
    DEFAULT_USE_HTTPS,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
)
from .cudy_client import CudyClient, CudyClientAuthError, CudyClientConnectionError

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_USERNAME, default=""): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_USE_HTTPS, default=DEFAULT_USE_HTTPS): bool,
        vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    _LOGGER.debug(
        "Validating input: host=%s, use_https=%s, verify_ssl=%s, username=%s",
        data[CONF_HOST],
        data.get(CONF_USE_HTTPS, DEFAULT_USE_HTTPS),
        data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
        data.get(CONF_USERNAME, "") or "(empty)",
    )
    
    client = CudyClient(
        host=data[CONF_HOST],
        password=data[CONF_PASSWORD],
        username=data.get(CONF_USERNAME, ""),
        use_https=data.get(CONF_USE_HTTPS, DEFAULT_USE_HTTPS),
        verify_ssl=data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
    )

    try:
        # Test connection and login
        _LOGGER.debug("Attempting login to %s", data[CONF_HOST])
        login_result = await client.login()
        if not login_result:
            _LOGGER.warning(
                "Login failed for %s - check password and ensure router is accessible (platform=%s, session_id=%s)",
                data[CONF_HOST],
                client.platform,
                client.session_id[:20] + "..." if client.session_id else None,
            )
            raise InvalidAuth("Authentication failed. Please check your password.")
        
        _LOGGER.debug("Login successful, platform=%s, session_id=%s...", client.platform, client.session_id[:20] if client.session_id else None)

        # Get device status to extract identity
        _LOGGER.debug("Fetching device status")
        status = await client.get_status()
        if not status:
            _LOGGER.warning("Status retrieval failed after successful login")
            raise CannotConnect

        model = status.get("model", "Unknown")
        _LOGGER.debug("Device model: %s", model)
        
        _LOGGER.debug("Fetching firmware information")
        firmware = await client.get_firmware_info()
        firmware_version = firmware.get("version") if firmware else None
        _LOGGER.debug("Firmware version: %s", firmware_version)

        # Try to get clients to extract MAC/serial for stable unique_id
        mac_address = None
        serial_number = None
        
        _LOGGER.debug("Attempting to fetch clients list for MAC/serial extraction")
        try:
            clients = await client.get_clients()
            if clients and isinstance(clients, list) and len(clients) > 0:
                _LOGGER.debug("Found %d client(s) in list", len(clients))
                # First client is usually the router itself
                first_client = clients[0]
                if isinstance(first_client, dict):
                    mac_address = first_client.get("macaddr")
                    serial_number = first_client.get("sn")
                    _LOGGER.debug("First client MAC: %s, Serial: %s", mac_address, serial_number)
                    # Also check sysreport for MAC
                    sysreport = first_client.get("sysreport", {})
                    if isinstance(sysreport, dict) and not mac_address:
                        mac_address = sysreport.get("macaddr")
                        _LOGGER.debug("MAC from sysreport: %s", mac_address)
            else:
                _LOGGER.debug("Clients list is empty or not a list")
        except Exception as err:
            # If clients fetch fails, continue with model-based ID
            _LOGGER.debug("Clients fetch failed (non-critical): %s", err, exc_info=True)

        # Generate stable unique_id: prefer MAC > serial > model+host
        if mac_address:
            unique_id = mac_address.replace(":", "").upper()
            _LOGGER.debug("Using MAC address for unique_id: %s", unique_id)
        elif serial_number:
            unique_id = serial_number
            _LOGGER.debug("Using serial number for unique_id: %s", unique_id)
        else:
            # Fallback to model+host (not stable across IP changes)
            unique_id = f"{model}_{data[CONF_HOST]}"
            _LOGGER.warning("Using fallback unique_id (model+host) - not stable across IP changes: %s", unique_id)

        await client.close()

        return {
            "title": f"{model} ({data[CONF_HOST]})",
            "unique_id": unique_id,
            "model": model,
            "firmware_version": firmware_version,
            "mac_address": mac_address,
            "serial_number": serial_number,
        }
    except InvalidAuth:
        # Re-raise InvalidAuth as-is
        raise
    except CannotConnect:
        # Re-raise CannotConnect as-is
        raise
    except CudyClientAuthError as err:
        raise InvalidAuth from err
    except CudyClientConnectionError as err:
        raise CannotConnect from err
    except Exception as err:
        _LOGGER.exception("Unexpected exception: %s", err)
        raise CannotConnect from err


class CudyScannerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Cudy Scanner."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Check if already configured
                await self.async_set_unique_id(info["unique_id"])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
