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
        try:
            # Ensure we're logged in
            if not self.client.session_id:
                if not await self.client.login():
                    raise UpdateFailed("Failed to login")

            # Fetch status
            status = await self.client.get_status()
            if not status:
                raise UpdateFailed("Failed to get status")

            # Fetch statistics (for WAN IP)
            statistics = await self.client.get_statistics()
            wan_ip = None
            if statistics and isinstance(statistics, dict):
                wan = statistics.get("wan", {})
                if isinstance(wan, dict):
                    wan_ip = wan.get("ipaddr")

            # Fetch firmware (less frequently, but include in update)
            firmware = await self.client.get_firmware_info()

            return {
                "model": status.get("model"),
                "firmware_version": firmware.get("version") if firmware else None,
                "firmware_hardware": firmware.get("hardware") if firmware else None,
                "wan_ip": wan_ip,
                "uptime": status.get("uptime"),
                "uptime_seconds": status.get("uptime_seconds"),
                "statistics": statistics,
            }

        except CudyClientAuthError as err:
            # Clear session and raise auth error
            self.client.session_id = None
            raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
        except CudyClientConnectionError as err:
            # On connection error, clear session to force re-login on next attempt
            self.client.session_id = None
            raise UpdateFailed(f"Connection error: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err

    async def async_reboot(self) -> bool:
        """Reboot the router."""
        # Check cooldown
        if self._last_reboot:
            from time import time

            if time() - self._last_reboot < 60:  # 60 second cooldown
                _LOGGER.warning("Reboot cooldown active, please wait")
                return False

        try:
            result = await self.client.reboot()
            if result:
                from time import time

                self._last_reboot = time()
                # Clear session - router will reboot
                self.client.session_id = None
                return True
        except Exception as err:
            _LOGGER.error("Reboot failed: %s", err)
            return False

        return False

