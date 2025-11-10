# Changelog

All notable changes to the Cudy Scanner integration will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive debug logging throughout integration
- Validation report with skeptical validation framework
- CHANGELOG.md for version tracking

### Changed
- Improved error messages in config flow
- Enhanced logging for troubleshooting

### Fixed
- 403 response handling for login page (now accepted as valid)
- Token extraction regex to handle class attributes
- Documentation contradictions resolved

## [0.1.0] - 2025-11-09

### Added
- Initial release with core MVP features
- LuCI authentication with double SHA256 password hashing
- Status sensors (firmware version, WAN IP, uptime)
- Binary sensor for online status
- Reboot button with 60-second cooldown
- Reboot service (`cudy_scanner.reboot`)
- Stable device identity using MAC address or serial number
- Per-device credentials support
- Diagnostics with sensitive data redaction
- Basic error recovery (session clearing on connection errors)

### Technical Details
- Platform: LuCI (OpenWrt-based web interface)
- Authentication: Session-based with CSRF token handling
- Update intervals: 10s (status), 15s (statistics)
- Local polling only (no cloud dependency)

### Known Limitations
- Manual IP entry required (discovery not implemented)
- No automatic IP change rediscovery (device identity is stable)
- Needs validation testing with real hardware

---

## Version History

- **0.1.0** (2025-11-09): Initial MVP release

