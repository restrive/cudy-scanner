# Cudy Scanner – Project Scope (v0.1)

Meta
- Date: 2025-11-07
- Project: Smart Home → HACS plugins → cudy-scanner
- Owner: George Gericke
- Path: `projects/smart-home/hacs-plugins/cudy-scanner/`

## Objective
Build a Home Assistant custom integration (HACS) to connect to Cudy routers (e.g., WR6500, WR3600) on the local network for discovery, status, and safe management actions (reboot), with resilience to IP changes and per-device credentials.

## In Scope (MVP)
- Discovery on local network and manual add by IP
  - Manual add via Config Flow (host/IP, username, password)
  - Optional discovery: SSDP/mDNS fingerprint where available; banner/HTTP probe fallback
- Resilience to IP changes
  - Persist stable identity (MAC/serial/model) and re-resolve via ARP/SSDP/mDNS when host unreachable
  - Periodic DNS/hostname re-resolution when configured via hostname
- Per-device credentials
  - Store credentials per `config_entry` (each router has its own login)
  - Diagnostics with credential redaction
- Reboot action
  - Expose a guarded service/button to reboot device (with confirmation/rate-limit)
- Device status
  - Expose basic sensors: online state, uptime (if available), firmware/version, WAN IP
  - DataUpdateCoordinator cadence with graceful errors/backoff

## Out of Scope (MVP)
- Firmware update/rollback
- Deep configuration changes (SSID, firewall rules, parental controls)
- Cloud/app remote control
- Multi-controller/mesh topology management beyond primary device status

## Assumptions & Constraints
- Local network access from Home Assistant host to router(s)
- HTTP(S) web UI or local API available; no reliance on cloud
- Some models may differ by firmware (OpenWrt/LuCI/ubus vs proprietary)
- Prefer minimal polling to avoid UI lockouts; implement rate limiting

## Architecture Overview
- Integration type: `hub`; local polling with `DataUpdateCoordinator`
- Identity: Prefer MAC address and model/serial; map identity → current IP
- Auth: Session or token-based login; SSL verify toggle for self-signed certs
- Discovery: SSDP/mDNS where possible; fallback to targeted HTTP banner check
- Entities: `sensor` (uptime, firmware, WAN IP), optional `binary_sensor` (online)
- Services: `cudy_scanner.reboot` (guarded), future: diagnostics dump
- Diagnostics: redact `password`/tokens; include model/firmware, last errors

## Acceptance Criteria
- Manual add: User can add router with host/IP and credentials via Config Flow
- Discovery: Integration can suggest devices found via SSDP/mDNS when available
- IP change resilience: If the router IP changes, integration re-associates and recovers without re-adding
- Per-device credentials: Multiple routers with distinct logins coexist; diagnostics redact secrets
- Reboot: A visible, confirmable action exists; router reboots successfully (happy path) and errors are surfaced
- Status: Uptime (if provided), firmware/version string, and WAN IP exposed as entities; coordinator updates without blocking HA

## Risks & Mitigations
- CSRF/rotating tokens: Centralize token extraction and refresh logic
- Session expiry/lockout: Bounded retries, exponential backoff, and cooldowns
- Model divergence: Feature-gate endpoints by detected model/firmware
- IP churn: Maintain identity mapping (MAC/serial) and rediscovery routine
- SSL issues: User-controlled SSL verify; document security implications

## Security & Privacy
- Store credentials in `config_entry.data` only; do not log secrets
- Diagnostics redact `password`, tokens, serials if sensitive
- Local-only communication; no data leaves LAN

## Testing & QA (MVP)
- Config Flow: invalid host/auth, unreachable, success
- Status polling: router online/offline transitions, backoff behavior
- IP change: simulate IP change and verify automatic recovery
- Reboot: confirm action with throttle; ensure HA stays responsive

## Milestones
- M1: Config Flow + manual add + diagnostics skeleton
- M2: Status sensors with coordinator + logging/backoff
- M3: Reboot service with confirmation/rate limiting
- M4: IP change resilience (identity mapping + rediscovery)
- M5: Optional discovery (SSDP/mDNS) + docs

## Open Questions
- Do WR6500/WR3600 expose ubus/LuCI or proprietary endpoints?
- Preferred discovery method in the target LAN (SSDP available?)
- Minimum polling intervals to avoid admin UI lockouts

## Deep Thought Additions (Essential Items)
- Nuance cues: per-model firmware variance; CSRF; captive portal redirects; lockout thresholds
- Implementation intentions: If 401 → refresh session; If 5xx → backoff; If unreachable → run rediscovery
- Rate limiting: Global semaphore on requests; jittered coordinator intervals
- Governance: Security review for diagnostics redaction; feature flags per model; change log
- Perspective checks: User safety on reboot (confirmations), privacy of logs, multi-user HA setups
- Pre-mortem highlights: Token parsing breaks on update; discovery floods network; IP change not detected

Links
- Plan: `experts/task-builder/tasks/cudy-scanner.hacs-plugin.20251107.v0.1.md`
- Research: `docs/research/smart-home-cudy-scanner/router-ap-hacs-integrations-survey.20251107.v0.1.md`

