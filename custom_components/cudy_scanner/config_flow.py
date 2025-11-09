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
    client = CudyClient(
        host=data[CONF_HOST],
        password=data[CONF_PASSWORD],
        username=data.get(CONF_USERNAME, ""),
        use_https=data.get(CONF_USE_HTTPS, DEFAULT_USE_HTTPS),
        verify_ssl=data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
    )

    try:
        # Test connection and login
        login_result = await client.login()
        if not login_result:
            _LOGGER.warning("Login returned False - authentication may have failed")
            raise InvalidAuth

        # Get device status to extract identity
        status = await client.get_status()
        if not status:
            _LOGGER.warning("Status retrieval failed after successful login")
            raise CannotConnect

        model = status.get("model", "Unknown")
        firmware = await client.get_firmware_info()
        firmware_version = firmware.get("version") if firmware else None

        # Try to get clients to extract MAC/serial for stable unique_id
        mac_address = None
        serial_number = None
        
        try:
            clients = await client.get_clients()
            if clients and isinstance(clients, list) and len(clients) > 0:
                # First client is usually the router itself
                first_client = clients[0]
                if isinstance(first_client, dict):
                    mac_address = first_client.get("macaddr")
                    serial_number = first_client.get("sn")
                    # Also check sysreport for MAC
                    sysreport = first_client.get("sysreport", {})
                    if isinstance(sysreport, dict) and not mac_address:
                        mac_address = sysreport.get("macaddr")
        except Exception:
            # If clients fetch fails, continue with model-based ID
            pass

        # Generate stable unique_id: prefer MAC > serial > model+host
        if mac_address:
            unique_id = mac_address.replace(":", "").upper()
        elif serial_number:
            unique_id = serial_number
        else:
            # Fallback to model+host (not stable across IP changes)
            unique_id = f"{model}_{data[CONF_HOST]}"

        await client.close()

        return {
            "title": f"{model} ({data[CONF_HOST]})",
            "unique_id": unique_id,
            "model": model,
            "firmware_version": firmware_version,
            "mac_address": mac_address,
            "serial_number": serial_number,
        }
    except CudyClientAuthError as err:
        raise InvalidAuth from err
    except CudyClientConnectionError as err:
        raise CannotConnect from err
    except Exception as err:
        _LOGGER.exception("Unexpected exception")
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
