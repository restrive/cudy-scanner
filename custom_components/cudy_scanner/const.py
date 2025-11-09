"""Constants for Cudy Scanner integration."""

DOMAIN = "cudy_scanner"

# Configuration keys
CONF_HOST = "host"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_USE_HTTPS = "use_https"
CONF_VERIFY_SSL = "verify_ssl"

# Defaults
DEFAULT_USERNAME = ""
DEFAULT_USE_HTTPS = False
DEFAULT_VERIFY_SSL = False
DEFAULT_TIMEOUT = 10

# Update intervals (seconds)
UPDATE_INTERVAL_STATUS = 10
UPDATE_INTERVAL_STATISTICS = 15
UPDATE_INTERVAL_CLIENTS = 60
UPDATE_INTERVAL_FIRMWARE = 300  # Firmware rarely changes

# Reboot cooldown (seconds)
REBOOT_COOLDOWN = 60

# Platform identifiers
PLATFORM_LUCI = "luci"
PLATFORM_UBUS = "ubus"
PLATFORM_PROPRIETARY = "proprietary"

# LuCI static tokens (discovered from API recon)
LUC_TOKEN = "94496a67f83514ae84c0ad5c1ca8bab1"
LUC_SALT = "58253912f9629639f31d58724d9f0709"
