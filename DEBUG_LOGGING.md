# Debug Logging Documentation

**Date:** 2025-11-09  
**Status:** ✅ Comprehensive debug logging added throughout integration

## Overview

Comprehensive debug logging has been added throughout the Cudy Scanner integration to aid in troubleshooting and diagnostics. All sensitive data (passwords, full session IDs) is excluded from logs.

## Logging Levels

- **DEBUG**: Detailed diagnostic information (step-by-step operations)
- **INFO**: Important operational events (successful login, reboot)
- **WARNING**: Non-critical issues (cooldowns, fallbacks)
- **ERROR**: Errors with full stack traces (`exc_info=True`)

## Logging Coverage

### Client Initialization (`cudy_client.py`)

**Location:** `CudyClient.__init__()`
- Logs: host, protocol, verify_ssl, timeout, username
- **Excludes:** password

### Login Process (`cudy_client.py`)

**Location:** `_login_luci()`

**Step 1: Fetch Login Page**
- URL being fetched
- Response status code
- Response headers
- Body length

**Token Extraction**
- CSRF token (truncated to 20 chars)
- Token (truncated to 20 chars)
- Salt (truncated to 20 chars)
- Whether each token was found in HTML

**Password Hashing**
- Hash length
- Algorithm used (sha256(sha256(pwd+salt)+token))
- **Excludes:** actual password or hashed password

**Step 2: POST Login**
- POST URL
- Response status
- Response headers
- Cookies received (truncated)
- Session ID (truncated to 20 chars)
- Redirect location (if 302)

**Login Failure**
- Detailed reason (no sysauth cookie, wrong status, etc.)

### Status Retrieval (`cudy_client.py`)

**Location:** `_get_status_luci()`
- Session ID (truncated)
- Request URL
- Response status
- Body length
- Extracted model
- Extracted uptime string
- Parsed uptime in seconds
- Final status data dictionary

### Firmware Retrieval (`cudy_client.py`)

**Location:** `_get_firmware_luci()`
- Session ID (truncated)
- Request URL
- Response status
- Body length
- Extracted firmware version
- Extracted hardware
- Final firmware data

### Statistics Retrieval (`cudy_client.py`)

**Location:** `_get_statistics_luci()`
- Session ID (truncated)
- Request URL
- Response status
- JSON keys (if JSON response)
- HTML body length (if HTML fallback)
- Data format (JSON vs HTML)

### Clients Retrieval (`cudy_client.py`)

**Location:** `_get_clients_luci()`
- Session ID (truncated)
- Request URL
- Response status
- Number of clients found
- Data format (JSON vs HTML)
- HTML body length (if HTML fallback)

### Reboot Process (`cudy_client.py`)

**Location:** `_reboot_luci()`

**Step 1: GET Reboot Page**
- Request URL
- Response status
- Body length
- Token extraction success/failure
- Extracted token (truncated to 20 chars)
- Generated timeclock

**Step 2: POST Reboot Form**
- Response status
- Form data fields (without sensitive values)

**Step 3: GET Apply Endpoint**
- Request URL
- Response status
- Success/failure

### Config Flow (`config_flow.py`)

**Location:** `validate_input()`
- Input parameters (host, use_https, verify_ssl, username)
- Login attempt start
- Login result (success/failure with platform and session_id)
- Device status fetch
- Model extraction
- Firmware version extraction
- Clients list fetch attempt
- MAC address extraction
- Serial number extraction
- Unique ID generation method (MAC/serial/fallback)
- **Excludes:** password

### Coordinator Updates (`coordinator.py`)

**Location:** `_async_update_data()`
- Data update start (with host)
- Session status (existing vs new login)
- Status fetch
- Statistics fetch
- WAN IP extraction
- Firmware fetch
- Final data dictionary (excluding large statistics object)
- Error details with stack traces

**Location:** `async_reboot()`
- Reboot request (with host)
- Cooldown check (time since last reboot)
- Remaining cooldown time (if active)
- Reboot command send
- Success/failure with details

## Example Log Output

### Successful Login
```
DEBUG: Starting login process for http://192.168.20.2
DEBUG: Attempting LuCI login
DEBUG: Step 1: Fetching login page from http://192.168.20.2/cgi-bin/luci/
DEBUG: Login page response: status=200, headers={...}
DEBUG: Login page body length: 15234 characters
DEBUG: Extracted tokens: _csrf=abc123... (found=True), token=94496a67... (found=True), salt=58253912... (found=True)
DEBUG: Generated dynamic fields: zonename=UTC, timeclock=1731234567
DEBUG: Password hashed (length=64, algorithm=sha256(sha256(pwd+salt)+token))
DEBUG: Step 2: POSTing login form to http://192.168.20.2/cgi-bin/luci/admin/login
DEBUG: Login POST response: status=302, headers={...}, cookies={sysauth: 57dcdfc9...}
INFO: LuCI login successful - session_id=57dcdfc92078f8c3a082...
INFO: Login successful via LuCI platform
```

### Data Update
```
DEBUG: Starting data update for 192.168.20.2
DEBUG: Using existing session_id=57dcdfc92078f8c3a082...
DEBUG: Fetching router status
DEBUG: Getting status with session_id=57dcdfc92078f8c3a082...
DEBUG: Fetching status from http://192.168.20.2/cgi-bin/luci/admin/status
DEBUG: Status response: status=200
DEBUG: Status page body length: 12345 characters
DEBUG: Extracted model: WR3600
DEBUG: Extracted uptime: 2d 3h 45m (198900 seconds)
DEBUG: Status retrieved: {'model': 'WR3600', 'uptime': '2d 3h 45m', 'uptime_seconds': 198900}
DEBUG: Fetching network statistics
DEBUG: Statistics retrieved as JSON (keys: ['wan', 'lan', ...])
DEBUG: WAN IP extracted: 192.168.20.2
DEBUG: Fetching firmware information
DEBUG: Firmware info: {'version': '2.3.15-20250905-182353', 'hardware': 'WR3600 V1.0'}
DEBUG: Data update complete: {'model': 'WR3600', 'firmware_version': '2.3.15-20250905-182353', 'wan_ip': '192.168.20.2', 'uptime': '2d 3h 45m', 'uptime_seconds': 198900}
```

### Reboot Process
```
INFO: Reboot requested for 192.168.20.2 (platform=luci)
DEBUG: Reboot with session_id=57dcdfc92078f8c3a082...
DEBUG: Step 1: Fetching reboot page from http://192.168.20.2/cgi-bin/luci/admin/system/reboot/reboot
DEBUG: Reboot page response: status=200
DEBUG: Reboot page body length: 8765 characters
DEBUG: Extracted reboot token: dd8e208a830e44e22b4f..., timeclock=1731234567
DEBUG: Step 2: POSTing reboot form
DEBUG: Reboot POST response: status=200
DEBUG: Step 3: Triggering reboot via http://192.168.20.2/cgi-bin/luci/admin/system/reboot/apply
DEBUG: Reboot apply response: status=200
INFO: Reboot command sent successfully to 192.168.20.2
```

## Enabling Debug Logging

To enable debug logging in Home Assistant:

1. Go to **Settings** → **System** → **Logs**
2. Click **Download Full Home Assistant Log**
3. Or add to `configuration.yaml`:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.cudy_scanner: debug
   ```
4. Restart Home Assistant

## Security Notes

- **Passwords**: Never logged (not in debug, info, warning, or error logs)
- **Session IDs**: Truncated to first 20 characters in logs
- **Tokens**: Truncated to first 20 characters in logs
- **Hashed Passwords**: Not logged (only hash length and algorithm)
- **Full URLs**: Logged (may contain IP addresses, but no credentials)

## Troubleshooting with Logs

### Authentication Issues
Look for:
- `Login page response: status=XXX` - Check if router is reachable
- `Extracted tokens: ... (found=False)` - HTML structure may have changed
- `Login POST did not result in successful authentication` - Password may be wrong or tokens invalid

### Connection Issues
Look for:
- `Connection error: ...` - Network connectivity problem
- `SSL certificate verification failed` - SSL/HTTPS configuration issue
- `Request to ... timed out` - Router may be offline or slow

### Data Retrieval Issues
Look for:
- `Status request returned status XXX` - Session may have expired
- `Statistics not available or invalid format` - Endpoint may have changed
- `Uptime not found in status page` - HTML parsing pattern may need update

### Reboot Issues
Look for:
- `Reboot page returned status XXX` - Access denied or session expired
- `Token not found in reboot page` - HTML structure changed
- `Reboot POST returned status XXX` - Form submission failed
- `Reboot apply returned status XXX` - Reboot trigger failed

## Log File Locations

- **Home Assistant Logs**: Available via UI (Settings → System → Logs)
- **Full Log Download**: Includes all debug information
- **Diagnostics Export**: Redacted version (passwords/tokens removed)

---

**Last Updated:** 2025-11-09  
**Coverage:** Complete - All major operations logged with debug details

