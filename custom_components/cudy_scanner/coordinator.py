"""DataUpdateCoordinator for Cudy Scanner."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    UPDATE_INTERVAL_FIRMWARE,
    UPDATE_INTERVAL_STATISTICS,
    UPDATE_INTERVAL_STATUS,
)
from .cudy_client import CudyClient, CudyClientAuthError, CudyClientConnectionError

_LOGGER = logging.getLogger(__name__)


class CudyScannerCoordinator(DataUpdateCoordinator):
    """Coordinator for Cudy Scanner data updates."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: CudyClient,
        update_interval: int = UPDATE_INTERVAL_STATUS,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Cudy Scanner",
            update_interval=timedelta(seconds=update_interval),
        )
        self.client = client
        self._last_reboot: float | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from router."""
        _LOGGER.debug("Starting data update for %s", self.client.host)
        try:
            # Ensure we're logged in
            if not self.client.session_id:
                _LOGGER.debug("No session ID, attempting login")
                if not await self.client.login():
                    _LOGGER.error("Login failed during data update")
                    raise UpdateFailed("Failed to login")
                _LOGGER.debug("Login successful, session_id=%s...", self.client.session_id[:20] if self.client.session_id else None)
            else:
                _LOGGER.debug("Using existing session_id=%s...", self.client.session_id[:20])

            # Fetch status
            _LOGGER.debug("Fetching router status")
            status = await self.client.get_status()
            if not status:
                _LOGGER.error("Status retrieval returned None")
                raise UpdateFailed("Failed to get status")
            _LOGGER.debug("Status retrieved: %s", status)

            # Fetch statistics (for WAN IP)
            _LOGGER.debug("Fetching network statistics")
            statistics = await self.client.get_statistics()
            wan_ip = None
            if statistics and isinstance(statistics, dict):
                wan = statistics.get("wan", {})
                if isinstance(wan, dict):
                    wan_ip = wan.get("ipaddr")
                    _LOGGER.debug("WAN IP extracted: %s", wan_ip)
            else:
                _LOGGER.debug("Statistics not available or invalid format")

            # Fetch firmware (less frequently, but include in update)
            _LOGGER.debug("Fetching firmware information")
            firmware = await self.client.get_firmware_info()
            _LOGGER.debug("Firmware info: %s", firmware)

            data = {
                "model": status.get("model"),
                "firmware_version": firmware.get("version") if firmware else None,
                "firmware_hardware": firmware.get("hardware") if firmware else None,
                "wan_ip": wan_ip,
                "uptime": status.get("uptime"),
                "uptime_seconds": status.get("uptime_seconds"),
                "statistics": statistics,
            }
            _LOGGER.debug("Data update complete: %s", {k: v for k, v in data.items() if k != "statistics"})
            return data

        except CudyClientAuthError as err:
            # Clear session and raise auth error
            _LOGGER.error("Authentication error during data update: %s", err, exc_info=True)
            self.client.session_id = None
            raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
        except CudyClientConnectionError as err:
            # On connection error, clear session to force re-login on next attempt
            _LOGGER.error("Connection error during data update: %s", err, exc_info=True)
            self.client.session_id = None
            raise UpdateFailed(f"Connection error: {err}") from err
        except Exception as err:
            _LOGGER.error("Unexpected error during data update: %s", err, exc_info=True)
            raise UpdateFailed(f"Error fetching data: {err}") from err

    async def async_reboot(self) -> bool:
        """Reboot the router."""
        _LOGGER.info("Reboot requested for %s", self.client.host)
        # Check cooldown
        if self._last_reboot:
            from time import time

            time_since_reboot = time() - self._last_reboot
            if time_since_reboot < 60:  # 60 second cooldown
                remaining = 60 - int(time_since_reboot)
                _LOGGER.warning("Reboot cooldown active, please wait %d more seconds", remaining)
                return False
            _LOGGER.debug("Cooldown period passed (%d seconds since last reboot)", int(time_since_reboot))

        try:
            _LOGGER.debug("Sending reboot command to router")
            result = await self.client.reboot()
            if result:
                from time import time

                self._last_reboot = time()
                # Clear session - router will reboot
                self.client.session_id = None
                _LOGGER.info("Reboot command sent successfully to %s", self.client.host)
                return True
            else:
                _LOGGER.warning("Reboot command returned False")
        except Exception as err:
            _LOGGER.error("Reboot failed: %s", err, exc_info=True)
            return False

        _LOGGER.warning("Reboot command failed")
        return False

