# Cudy Scanner (HACS)

A Home Assistant custom integration to connect to Cudy routers (WR3600, WR6500) on the local network, read configuration/status, and expose safe actions like reboot.

**Status:** ✅ MVP Complete - Ready for Testing  
**Version:** 0.1.0  
**Repository:** https://github.com/restrive/cudy-scanner

## Features

- ✅ **Local-only connectivity** to Cudy router admin UI/API (LuCI/OpenWrt-based)
- ✅ **Device discovery** via MAC address/serial number extraction
- ✅ **Stable device identity** - survives IP changes
- ✅ **Status sensors:**
  - Firmware version
  - WAN IP address
  - Uptime (duration)
- ✅ **Binary sensor:** Online status
- ✅ **Reboot button** with 60-second cooldown protection
- ✅ **Reboot service:** `cudy_scanner.reboot`
- ✅ **Per-device credentials** - each router has its own login
- ✅ **Diagnostics** with sensitive data redaction

## Installation

### Via HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations**
3. Click the three dots (⋮) in the top right
4. Select **Custom repositories**
5. Add repository: `https://github.com/restrive/cudy-scanner`
6. Select category: **Integration**
7. Click **Add**
8. Find **Cudy Scanner** in the integrations list
9. Click **Download**
10. Restart Home Assistant
11. Go to **Settings** → **Devices & Services**
12. Click **Add Integration** and search for **Cudy Scanner**

### Manual Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/restrive/cudy-scanner.git
   cd cudy-scanner
   ```

2. Copy the `custom_components` folder to your Home Assistant `config` directory:
   ```bash
   cp -r custom_components ~/.homeassistant/
   ```

3. Restart Home Assistant

4. Go to **Settings** → **Devices & Services** → **Add Integration** → **Cudy Scanner**

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **Cudy Scanner**
4. Enter your router details:
   - **Host/IP:** Router IP address (e.g., `192.168.1.1`)
   - **Username:** Usually empty (leave blank)
   - **Password:** Router admin password
   - **Use HTTPS:** Optional (default: HTTP)
   - **Verify SSL:** Optional (default: false for self-signed certs)

5. The integration will:
   - Test the connection
   - Extract device identity (MAC address or serial number)
   - Create entities automatically

## Usage

### Entities

After setup, the following entities are created:

- **Sensor: Firmware Version** - Current firmware version
- **Sensor: WAN IP** - Router's WAN IP address
- **Sensor: Uptime** - Router uptime (formatted as duration)
- **Binary Sensor: Online** - Connection status
- **Button: Reboot** - Reboot the router

### Services

#### Reboot Service

Reboot a Cudy router:

```yaml
service: cudy_scanner.reboot
data:
  device_id: "80AFCA8B8B8D"  # MAC address without colons (from device unique_id)
```

Or use the reboot button entity directly.

## Supported Models

- ✅ **WR3600** - Tested and working
- ✅ **WR6500** - Tested and working
- ⚠️ Other Cudy models with LuCI interface may work

## Requirements

- Home Assistant 2023.1.0 or later
- Local network access to router
- Router admin password

## Technical Details

- **Platform:** LuCI (OpenWrt-based web interface)
- **Authentication:** Session-based with double SHA256 password hashing
- **Update Interval:** 10 seconds (status), 15 seconds (statistics)
- **Polling:** Local polling (no cloud dependency)

## IP Change Resilience

The integration uses MAC address or serial number as stable device identifiers. If your router's IP changes:

1. The integration will detect the connection failure
2. Session will be cleared and re-login attempted
3. Device identity remains stable (based on MAC/serial)

**Note:** Full automatic rediscovery (ARP/SSDP) is planned for future releases.

## Troubleshooting

### Connection Issues

- Verify router IP address is correct
- Check router is accessible from Home Assistant host
- Verify password is correct (no username usually required)
- Check router firewall settings

### Authentication Errors

- Ensure password is correct
- Some routers may require username (try leaving blank first)
- Check router logs for login attempts

### Missing Data

- Check router is online
- Verify credentials are correct
- Check Home Assistant logs for errors
- Some data may not be available on all models

## Diagnostics

To help with troubleshooting, you can export diagnostics:

1. Go to **Settings** → **System** → **Diagnostics**
2. Select **Cudy Scanner** integration
3. Click **Download Diagnostics**

**Note:** All sensitive data (passwords, tokens) are automatically redacted.

## Development

### Repository Structure

```
cudy-scanner/
├── custom_components/
│   └── cudy_scanner/
│       ├── __init__.py
│       ├── config_flow.py
│       ├── coordinator.py
│       ├── cudy_client.py
│       ├── sensor.py
│       ├── binary_sensor.py
│       ├── button.py
│       └── ...
├── docs/
├── research/
└── README.md
```

### Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Roadmap

- [ ] SSDP/UPnP discovery
- [ ] mDNS discovery
- [ ] Full IP change rediscovery (ARP/SSDP)
- [ ] Options flow for polling intervals
- [ ] Connected clients device tracker
- [ ] Mesh topology visualization
- [ ] Firmware update checking

## License

[Add your license here]

## Acknowledgments

- Based on reverse engineering of Cudy router LuCI interface
- Inspired by other router/AP integrations in HACS

## Support

- **Issues:** https://github.com/restrive/cudy-scanner/issues
- **Repository:** https://github.com/restrive/cudy-scanner

---

**Version:** 0.1.0  
**Last Updated:** 2025-11-09  
**Status:** MVP Complete - Ready for Testing
