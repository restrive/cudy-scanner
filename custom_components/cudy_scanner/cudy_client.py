"""Async Cudy Router API Client for Home Assistant."""

from __future__ import annotations

import hashlib
import logging
import re
import time
from typing import Any

import aiohttp
from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientSSLError

from .const import (
    DEFAULT_TIMEOUT,
    DEFAULT_USE_HTTPS,
    DEFAULT_VERIFY_SSL,
    LUC_SALT,
    LUC_TOKEN,
    PLATFORM_LUCI,
)

_LOGGER = logging.getLogger(__name__)


class CudyClientError(Exception):
    """Base exception for Cudy client errors."""


class CudyClientAuthError(CudyClientError):
    """Authentication error."""


class CudyClientConnectionError(CudyClientError):
    """Connection error."""


class CudyClient:
    """Async client for interacting with Cudy router web UI/API."""

    def __init__(
        self,
        host: str,
        password: str,
        username: str = "",
        use_https: bool = DEFAULT_USE_HTTPS,
        verify_ssl: bool = DEFAULT_VERIFY_SSL,
        timeout: int = DEFAULT_TIMEOUT,
        session: ClientSession | None = None,
    ) -> None:
        """Initialize client.

        Args:
            host: Router IP or hostname
            password: Admin password
            username: Admin username (optional, usually empty)
            use_https: Use HTTPS (default: HTTP)
            verify_ssl: Verify SSL certificates
            timeout: Request timeout in seconds
            session: Optional aiohttp session (for connection pooling)
        """
        self.host = host
        self.username = username
        self.password = password
        self.protocol = "https" if use_https else "http"
        self.base_url = f"{self.protocol}://{host}"
        self.verify_ssl = verify_ssl
        self.timeout = ClientTimeout(total=timeout)
        self._session = session
        self._own_session = False

        self.session_id: str | None = None
        self.csrf_token: str | None = None
        self.platform: str | None = None
        
        _LOGGER.debug(
            "Initialized CudyClient: host=%s, protocol=%s, verify_ssl=%s, timeout=%s, username=%s",
            host,
            self.protocol,
            verify_ssl,
            timeout,
            username if username else "(empty)",
        )

    async def _ensure_session(self) -> ClientSession:
        """Ensure we have a session."""
        if self._session is None or self._session.closed:
            # Handle SSL verification properly
            # For aiohttp, ssl=False disables verification, ssl=True enables it
            if self.verify_ssl:
                ssl_setting = True  # Use default SSL verification
            else:
                # Disable SSL verification for self-signed certificates
                ssl_setting = False
            
            self._session = ClientSession(
                timeout=self.timeout,
                connector=aiohttp.TCPConnector(ssl=ssl_setting),
            )
            self._own_session = True
        return self._session

    async def close(self) -> None:
        """Close the session if we own it."""
        if self._own_session and self._session and not self._session.closed:
            await self._session.close()

    def _hash_password(self, password: str, salt: str, token: str) -> str:
        """Hash password using double SHA256 with salt and token.

        Algorithm: sha256(sha256(password + salt) + token)
        """
        # Step 1: sha256(password + salt)
        hash1 = hashlib.sha256((password + salt).encode("utf-8")).hexdigest()
        # Step 2: sha256(hash1 + token)
        hashed = hashlib.sha256((hash1 + token).encode("utf-8")).hexdigest()
        return hashed

    async def login(self) -> bool:
        """Login to router and establish session."""
        _LOGGER.debug("Starting login process for %s", self.base_url)
        session = await self._ensure_session()

        # Detect platform by trying LuCI first
        _LOGGER.debug("Attempting LuCI login")
        if await self._login_luci(session):
            self.platform = PLATFORM_LUCI
            _LOGGER.info("Login successful via LuCI platform")
            return True

        _LOGGER.warning("LuCI login failed, no other platforms available")
        # TODO: Add ubus and proprietary login methods
        return False

    async def _login_luci(self, session: ClientSession) -> bool:
        """Login via LuCI interface."""
        try:
            # Step 1: GET login page to extract tokens
            login_url = f"{self.base_url}/cgi-bin/luci/"
            _LOGGER.debug("Step 1: Fetching login page from %s", login_url)
            headers = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-ZA,en;q=0.9",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }

            async with session.get(login_url, headers=headers, allow_redirects=False) as resp:
                _LOGGER.debug("Login page response: status=%s, headers=%s", resp.status, dict(resp.headers))
                # 403 is valid - it means the page requires authentication (which is expected for login page)
                if resp.status not in (200, 302, 403):
                    _LOGGER.warning("Login page returned unexpected status: %s", resp.status)
                    return False

                body = await resp.text()
                _LOGGER.debug("Login page body length: %d characters", len(body))
                
                # If we got 403, the page is still accessible and contains the login form
                if resp.status == 403:
                    _LOGGER.debug("Login page returned 403 (expected - requires authentication)")

                # Extract tokens from HTML
                # Updated regex to handle class attributes between name and value (as in explorer)
                csrf_match = re.search(
                    r'name=["\']?_csrf["\']?\s+[^>]*value=["\']?([^"\']+)', body, re.I
                )
                token_match = re.search(
                    r'name=["\']?token["\']?\s+[^>]*value=["\']?([^"\']+)', body, re.I
                )
                salt_match = re.search(
                    r'name=["\']?salt["\']?\s+[^>]*value=["\']?([^"\']+)', body, re.I
                )

                _csrf = csrf_match.group(1) if csrf_match else ""
                token = token_match.group(1) if token_match else LUC_TOKEN
                salt = salt_match.group(1) if salt_match else LUC_SALT
                
                _LOGGER.debug(
                    "Extracted tokens: _csrf=%s (found=%s), token=%s (found=%s), salt=%s (found=%s)",
                    _csrf[:20] + "..." if len(_csrf) > 20 else _csrf,
                    bool(csrf_match),
                    token[:20] + "..." if len(token) > 20 else token,
                    bool(token_match),
                    salt[:20] + "..." if len(salt) > 20 else salt,
                    bool(salt_match),
                )

                # Generate dynamic fields
                # Use UTC timezone as default (most routers accept this)
                zonename = "UTC"
                timeclock = str(int(time.time()))
                _LOGGER.debug("Generated dynamic fields: zonename=%s, timeclock=%s", zonename, timeclock)

                # Hash password
                hashed_password = self._hash_password(self.password, salt, token)
                _LOGGER.debug("Password hashed (length=%d, algorithm=sha256(sha256(pwd+salt)+token))", len(hashed_password))
                _LOGGER.debug("Hash first 20 chars: %s...", hashed_password[:20])

                # Step 2: POST login
                login_post_url = f"{self.base_url}/cgi-bin/luci/admin/login"
                
                # Build form data
                form_data = aiohttp.FormData()
                form_data.add_field("_csrf", _csrf)
                form_data.add_field("token", token)
                if salt:  # Only include salt if we found it
                    form_data.add_field("salt", salt)
                form_data.add_field("luci_password", hashed_password)
                form_data.add_field("luci_username", self.username or "")
                form_data.add_field("zonename", zonename)
                form_data.add_field("timeclock", timeclock)
                
                # Log form data (without password)
                _LOGGER.debug(
                    "Login form data: _csrf=%s..., token=%s..., salt=%s..., luci_username=%s, zonename=%s, timeclock=%s, luci_password=[REDACTED]",
                    _csrf[:20] if len(_csrf) > 20 else _csrf,
                    token[:20] if len(token) > 20 else token,
                    salt[:20] if salt and len(salt) > 20 else salt,
                    self.username or "(empty)",
                    zonename,
                    timeclock,
                )

                post_headers = {
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-ZA,en;q=0.9",
                    "Cache-Control": "no-cache",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Origin": self.base_url,
                    "Pragma": "no-cache",
                    "Referer": login_url,
                    "Upgrade-Insecure-Requests": "1",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
                }
                
                _LOGGER.debug("POST headers: %s", {k: v for k, v in post_headers.items()})
                _LOGGER.debug("Step 2: POSTing login form to %s", login_post_url)
                
                async with session.post(
                    login_post_url, data=form_data, headers=post_headers, allow_redirects=False
                ) as post_resp:
                    response_headers = dict(post_resp.headers)
                    response_cookies = {k: v.value[:20] + "..." if len(v.value) > 20 else v.value for k, v in post_resp.cookies.items()}
                    
                    _LOGGER.debug(
                        "Login POST response: status=%s, content-type=%s",
                        post_resp.status,
                        response_headers.get("Content-Type", "unknown"),
                    )
                    _LOGGER.debug("Response headers: %s", response_headers)
                    _LOGGER.debug("Response cookies: %s", response_cookies)
                    
                    # Get response body for analysis
                    try:
                        response_body = await post_resp.text()
                        _LOGGER.debug("Response body length: %d characters", len(response_body))
                        
                        # Check for error messages in response
                        if "error" in response_body.lower() or "invalid" in response_body.lower() or "failed" in response_body.lower():
                            # Extract error message if present
                            error_match = re.search(r'(error|invalid|failed)[^<]*:?\s*([^<\n]{0,100})', response_body, re.I)
                            if error_match:
                                _LOGGER.warning("Error message in response: %s", error_match.group(0)[:200])
                        
                        # Log first 500 chars of response for debugging
                        _LOGGER.debug("Response body preview (first 500 chars): %s", response_body[:500])
                        
                        # Check for login form still present (indicates failure)
                        if "login" in response_body.lower() and "form" in response_body.lower():
                            _LOGGER.warning("Login form still present in response - authentication likely failed")
                        
                        # Check for Set-Cookie header
                        set_cookie_header = response_headers.get("Set-Cookie", "")
                        if set_cookie_header:
                            _LOGGER.debug("Set-Cookie header: %s", set_cookie_header[:200])
                            sysauth_in_header = "sysauth" in set_cookie_header.lower()
                            _LOGGER.debug("sysauth in Set-Cookie header: %s", sysauth_in_header)
                    except Exception as body_err:
                        _LOGGER.warning("Could not read response body: %s", body_err)
                        response_body = ""
                    
                    # Check for sysauth cookie
                    cookies = post_resp.cookies
                    _LOGGER.debug("Cookies object: %s", list(cookies.keys()))
                    if "sysauth" in cookies:
                        self.session_id = cookies["sysauth"].value
                        self.csrf_token = _csrf
                        _LOGGER.info("LuCI login successful - session_id=%s...", self.session_id[:20])
                        return True
                    else:
                        _LOGGER.debug("No sysauth cookie found in response cookies")

                    # Also check redirect away from login
                    if post_resp.status == 302:
                        location = post_resp.headers.get("Location", "")
                        _LOGGER.debug("Login POST returned 302 redirect to: %s", location)
                        if "login" not in location.lower():
                            # Try to extract sysauth from Set-Cookie header
                            set_cookie = post_resp.headers.get("Set-Cookie", "")
                            if set_cookie:
                                _LOGGER.debug("Checking Set-Cookie header for sysauth: %s", set_cookie[:200])
                            sysauth_match = re.search(r'sysauth=([^;]+)', set_cookie)
                            if sysauth_match:
                                self.session_id = sysauth_match.group(1)
                                self.csrf_token = _csrf
                                _LOGGER.info("LuCI login successful (redirect) - session_id=%s...", self.session_id[:20])
                                return True
                            else:
                                _LOGGER.debug("sysauth not found in Set-Cookie header")
                    
                    # Detailed failure analysis
                    _LOGGER.error(
                        "Login POST failed - status=%s, has_sysauth_cookie=%s, location=%s, set_cookie_header=%s",
                        post_resp.status,
                        "sysauth" in cookies,
                        post_resp.headers.get("Location", "none"),
                        bool(set_cookie_header),
                    )
                    
                    # If 403, provide specific guidance
                    if post_resp.status == 403:
                        _LOGGER.error(
                            "403 Forbidden on login POST - possible causes: "
                            "1) Password incorrect, 2) CSRF token invalid/expired, "
                            "3) Missing required form fields, 4) Rate limiting, "
                            "5) Router blocking automated requests"
                        )
                        # Check if we have all required fields
                        _LOGGER.debug(
                            "Form fields check: _csrf=%s, token=%s, salt=%s, has_password=%s, username=%s, zonename=%s, timeclock=%s",
                            bool(_csrf),
                            bool(token),
                            bool(salt),
                            bool(hashed_password),
                            bool(self.username or True),  # Username can be empty
                            bool(zonename),
                            bool(timeclock),
                        )

        except aiohttp.ClientSSLError as err:
            _LOGGER.error("LuCI login failed (SSL error): %s", err)
            raise CudyClientConnectionError(
                f"SSL certificate verification failed. Try disabling SSL verification or use HTTP instead of HTTPS."
            ) from err
        except aiohttp.ClientError as err:
            _LOGGER.error("LuCI login failed: %s", err)
            raise CudyClientConnectionError(f"Connection error: {err}") from err
        except Exception as err:
            _LOGGER.error("LuCI login failed: %s", err)
            return False

        return False

    async def get_status(self) -> dict[str, Any] | None:
        """Get router status (model)."""
        if not self.session_id:
            _LOGGER.warning("get_status called but not logged in")
            return None

        _LOGGER.debug("Fetching router status (platform=%s)", self.platform)
        if self.platform == PLATFORM_LUCI:
            return await self._get_status_luci()

        _LOGGER.warning("get_status: unsupported platform %s", self.platform)
        return None

    async def _get_status_luci(self) -> dict[str, Any] | None:
        """Get status via LuCI."""
        session = await self._ensure_session()
        session.cookie_jar.update_cookies({"sysauth": self.session_id})
        _LOGGER.debug("Getting status with session_id=%s...", self.session_id[:20] if self.session_id else "None")

        headers = {
            "Accept": "text/html, */*; q=0.01",
            "Referer": f"{self.base_url}/cgi-bin/luci/",
            "X-Requested-With": "XMLHttpRequest",
        }

        url = f"{self.base_url}/cgi-bin/luci/admin/status"
        _LOGGER.debug("Fetching status from %s", url)
        try:
            async with session.get(url, headers=headers) as resp:
                _LOGGER.debug("Status response: status=%s", resp.status)
                if resp.status == 200:
                    body = await resp.text()
                    _LOGGER.debug("Status page body length: %d characters", len(body))
                    status_data = {}
                    
                    # Extract model from title
                    model_match = re.search(r"<title>([^<]+)</title>", body, re.I)
                    if model_match:
                        status_data["model"] = model_match.group(1).strip()
                        _LOGGER.debug("Extracted model: %s", status_data["model"])
                    
                    # Extract uptime - look for common patterns
                    # Pattern 1: "Uptime" label followed by time
                    uptime_match = re.search(
                        r"Uptime[^<]*</label>[^<]*<[^>]*>([^<\n]+)",
                        body, re.I | re.DOTALL
                    )
                    if uptime_match:
                        uptime_str = uptime_match.group(1).strip()
                        status_data["uptime"] = uptime_str
                        # Try to parse to seconds
                        status_data["uptime_seconds"] = self._parse_uptime(uptime_str)
                        _LOGGER.debug("Extracted uptime: %s (%s seconds)", uptime_str, status_data.get("uptime_seconds"))
                    else:
                        _LOGGER.debug("Uptime not found in status page")
                    
                    _LOGGER.debug("Status data: %s", status_data)
                    return status_data if status_data else None
                else:
                    _LOGGER.warning("Status request returned status %s", resp.status)
        except Exception as err:
            _LOGGER.error("Status retrieval failed: %s", err, exc_info=True)

        return None

    def _parse_uptime(self, uptime_str: str) -> int | None:
        """Parse uptime string to seconds."""
        try:
            # Common formats: "1d 2h 3m 4s", "2h 30m", "45m", "30s"
            import re as re_module
            total_seconds = 0
            
            # Days
            days_match = re_module.search(r"(\d+)\s*d", uptime_str, re.I)
            if days_match:
                total_seconds += int(days_match.group(1)) * 86400
            
            # Hours
            hours_match = re_module.search(r"(\d+)\s*h", uptime_str, re.I)
            if hours_match:
                total_seconds += int(hours_match.group(1)) * 3600
            
            # Minutes
            minutes_match = re_module.search(r"(\d+)\s*m", uptime_str, re.I)
            if minutes_match:
                total_seconds += int(minutes_match.group(1)) * 60
            
            # Seconds
            seconds_match = re_module.search(r"(\d+)\s*s", uptime_str, re.I)
            if seconds_match:
                total_seconds += int(seconds_match.group(1))
            
            return total_seconds if total_seconds > 0 else None
        except Exception:
            return None

    async def get_firmware_info(self) -> dict[str, Any] | None:
        """Get firmware information."""
        if not self.session_id:
            _LOGGER.warning("get_firmware_info called but not logged in")
            return None

        _LOGGER.debug("Fetching firmware information (platform=%s)", self.platform)
        if self.platform == PLATFORM_LUCI:
            return await self._get_firmware_luci()

        _LOGGER.warning("get_firmware_info: unsupported platform %s", self.platform)
        return None

    async def _get_firmware_luci(self) -> dict[str, Any] | None:
        """Get firmware info via LuCI upgrade page."""
        session = await self._ensure_session()
        session.cookie_jar.update_cookies({"sysauth": self.session_id})

        headers = {
            "Accept": "text/html, */*; q=0.01",
            "Referer": f"{self.base_url}/cgi-bin/luci/admin/panel",
            "X-Requested-With": "XMLHttpRequest",
        }

        url = f"{self.base_url}/cgi-bin/luci/admin/system/upgrade"
        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    body = await resp.text()
                    firmware_data = {}

                    # Extract firmware version
                    version_match = re.search(
                        r"Firmware\s+Version[^<]*</label>[^<]*<[^>]*>([^<\n]+)",
                        body,
                        re.I | re.DOTALL,
                    )
                    if version_match:
                        firmware_data["version"] = version_match.group(1).strip()
                    else:
                        # Fallback
                        version_match = re.search(
                            r"form-control-static[^>]*>([\d\.\-]+)", body, re.I
                        )
                        if version_match:
                            firmware_data["version"] = version_match.group(1).strip()

                    # Extract hardware
                    hardware_match = re.search(
                        r"Hardware[^<]*</label>[^<]*<[^>]*>([^<\n]+)", body, re.I | re.DOTALL
                    )
                    if hardware_match:
                        firmware_data["hardware"] = hardware_match.group(1).strip()

                    return firmware_data if firmware_data else None
        except Exception as err:
            _LOGGER.error("Firmware retrieval failed: %s", err)

        return None

    async def get_statistics(self) -> dict[str, Any] | None:
        """Get network statistics (WAN IP, etc.)."""
        if not self.session_id:
            _LOGGER.warning("get_statistics called but not logged in")
            return None

        _LOGGER.debug("Fetching network statistics (platform=%s)", self.platform)
        if self.platform == PLATFORM_LUCI:
            return await self._get_statistics_luci()

        _LOGGER.warning("get_statistics: unsupported platform %s", self.platform)
        return None

    async def _get_statistics_luci(self) -> dict[str, Any] | None:
        """Get statistics via LuCI JSON endpoint."""
        session = await self._ensure_session()
        session.cookie_jar.update_cookies({"sysauth": self.session_id})
        _LOGGER.debug("Getting statistics with session_id=%s...", self.session_id[:20] if self.session_id else "None")

        headers = {
            "Accept": "*/*",
            "Referer": f"{self.base_url}/cgi-bin/luci/",
            "X-Requested-With": "XMLHttpRequest",
        }

        url = f"{self.base_url}/cgi-bin/luci/admin/status/statistic"
        _LOGGER.debug("Fetching statistics from %s", url)
        try:
            async with session.get(url, headers=headers) as resp:
                _LOGGER.debug("Statistics response: status=%s", resp.status)
                if resp.status == 200:
                    try:
                        data = await resp.json()
                        _LOGGER.debug("Statistics retrieved as JSON (keys: %s)", list(data.keys()) if isinstance(data, dict) else "not a dict")
                        return data
                    except Exception as json_err:
                        # Fallback to HTML parsing if not JSON
                        _LOGGER.debug("Statistics response is not JSON, parsing as HTML: %s", json_err)
                        body = await resp.text()
                        _LOGGER.debug("Statistics HTML body length: %d characters", len(body))
                        return {"raw": body[:1000]}
                else:
                    _LOGGER.warning("Statistics request returned status %s", resp.status)
        except Exception as err:
            _LOGGER.error("Statistics retrieval failed: %s", err, exc_info=True)

        return None

    async def get_clients(self) -> dict[str, Any] | None:
        """Get connected clients/device list."""
        if not self.session_id:
            _LOGGER.warning("get_clients called but not logged in")
            return None

        _LOGGER.debug("Fetching connected clients (platform=%s)", self.platform)
        if self.platform == PLATFORM_LUCI:
            return await self._get_clients_luci()

        _LOGGER.warning("get_clients: unsupported platform %s", self.platform)
        return None

    async def _get_clients_luci(self) -> dict[str, Any] | None:
        """Get connected clients via LuCI mesh/clients endpoint."""
        session = await self._ensure_session()
        session.cookie_jar.update_cookies({"sysauth": self.session_id})
        _LOGGER.debug("Getting clients with session_id=%s...", self.session_id[:20] if self.session_id else "None")

        headers = {
            "Accept": "*/*",
            "Referer": f"{self.base_url}/cgi-bin/luci/",
            "X-Requested-With": "XMLHttpRequest",
        }

        url = f"{self.base_url}/cgi-bin/luci/admin/network/mesh/clients"
        _LOGGER.debug("Fetching clients from %s", url)
        try:
            async with session.get(url, headers=headers) as resp:
                _LOGGER.debug("Clients response: status=%s", resp.status)
                if resp.status == 200:
                    try:
                        data = await resp.json()
                        _LOGGER.debug("Clients retrieved as JSON: %d client(s)", len(data) if isinstance(data, list) else "not a list")
                        return data
                    except Exception as json_err:
                        # Fallback to HTML parsing if not JSON
                        _LOGGER.debug("Clients response is not JSON, parsing as HTML: %s", json_err)
                        body = await resp.text()
                        _LOGGER.debug("Clients HTML body length: %d characters", len(body))
                        return {"raw": body[:2000], "format": "html"}
                else:
                    _LOGGER.warning("Clients request returned status %s", resp.status)
        except Exception as err:
            _LOGGER.error("Clients retrieval failed: %s", err, exc_info=True)

        return None

    async def reboot(self) -> bool:
        """Reboot the router."""
        if not self.session_id:
            _LOGGER.warning("reboot called but not logged in")
            return False

        _LOGGER.info("Reboot requested for %s (platform=%s)", self.host, self.platform)
        if self.platform == PLATFORM_LUCI:
            return await self._reboot_luci()

        _LOGGER.warning("reboot: unsupported platform %s", self.platform)
        return False

    async def _reboot_luci(self) -> bool:
        """Reboot via LuCI multi-step flow."""
        session = await self._ensure_session()
        session.cookie_jar.update_cookies({"sysauth": self.session_id})
        _LOGGER.debug("Reboot with session_id=%s...", self.session_id[:20] if self.session_id else "None")

        headers = {
            "Accept": "text/html, */*; q=0.01",
            "Referer": f"{self.base_url}/cgi-bin/luci/admin/panel",
            "X-Requested-With": "XMLHttpRequest",
        }

        try:
            # Step 1: GET reboot page to extract token
            reboot_url = f"{self.base_url}/cgi-bin/luci/admin/system/reboot/reboot"
            _LOGGER.debug("Step 1: Fetching reboot page from %s", reboot_url)
            async with session.get(reboot_url, headers=headers) as resp:
                _LOGGER.debug("Reboot page response: status=%s", resp.status)
                if resp.status != 200:
                    _LOGGER.warning("Reboot page returned status %s", resp.status)
                    return False

                body = await resp.text()
                _LOGGER.debug("Reboot page body length: %d characters", len(body))
                token_match = re.search(
                    r'name=["\']?token["\']?\s+value=["\']?([^"\']+)', body, re.I
                )
                if not token_match:
                    _LOGGER.warning("Token not found in reboot page")
                    return False

                token = token_match.group(1)
                timeclock = str(int(time.time()))
                _LOGGER.debug("Extracted reboot token: %s..., timeclock=%s", token[:20], timeclock)

                # Step 2: POST reboot form
                _LOGGER.debug("Step 2: POSTing reboot form")
                form_data = aiohttp.FormData()
                form_data.add_field("token", token)
                form_data.add_field("timeclock", timeclock)
                form_data.add_field("cbi.submit", "1")
                form_data.add_field("cbi.apply", "")

                post_headers = {
                    "Accept": "*/*",
                    "Content-Type": "multipart/form-data",
                    "Referer": f"{self.base_url}/cgi-bin/luci/admin/panel",
                    "X-Requested-With": "XMLHttpRequest",
                }

                async with session.post(
                    reboot_url, data=form_data, headers=post_headers
                ) as post_resp:
                    _LOGGER.debug("Reboot POST response: status=%s", post_resp.status)
                    if post_resp.status not in (200, 302):
                        _LOGGER.warning("Reboot POST returned status %s", post_resp.status)
                        return False

                    # Step 3: GET apply endpoint to trigger reboot
                    apply_url = f"{self.base_url}/cgi-bin/luci/admin/system/reboot/apply"
                    _LOGGER.debug("Step 3: Triggering reboot via %s", apply_url)
                    async with session.get(apply_url, headers=headers) as apply_resp:
                        _LOGGER.debug("Reboot apply response: status=%s", apply_resp.status)
                        if apply_resp.status in (200, 302):
                            _LOGGER.info("Reboot command sent successfully to %s", self.host)
                            return True
                        else:
                            _LOGGER.warning("Reboot apply returned status %s", apply_resp.status)

        except Exception as err:
            _LOGGER.error("Reboot failed: %s", err, exc_info=True)

        _LOGGER.warning("Reboot command failed")
        return False

