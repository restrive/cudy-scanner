# Cudy Scanner - Missing Items & Remaining Work

**Date:** 2025-11-09  
**Status:** Core MVP features implemented, discovery and advanced features missing

**Note:** This document may be partially outdated. See COMPLETED_FEATURES.md for what has been implemented.

## 🔴 Critical Missing Items (MVP Requirements)

### 1. Discovery Implementation
**Status:** ❌ Not implemented  
**Priority:** High (MVP requirement)

**Missing:**
- `async_step_ssdp()` - SSDP/UPnP discovery
- `async_step_zeroconf()` - mDNS discovery  
- HTTP banner probe fallback
- Device suggestion with model hints

**Files to create/modify:**
- `config_flow.py` - Add discovery steps
- May need `ssdp.py` helper if complex

**Reference:** Task #3, #10 in task list

---

### 2. IP Change Resilience
**Status:** ✅ Partially implemented (MAC/serial extraction working, rediscovery missing)  
**Priority:** High (MVP requirement)

**Implemented:**
- ✅ MAC address extraction from clients endpoint
- ✅ Serial number extraction from clients endpoint
- ✅ Stable unique_id based on MAC/serial (not host+model)
- ✅ Session cleared on connection failure

**Still Missing:**
- ❌ Automatic rediscovery mechanism on connection failure
- ❌ Config entry update with new IP when found
- ❌ ARP/SSDP/mDNS rediscovery integration

**Current state:**
- Unique ID is stable (MAC/serial) - survives IP changes
- No automatic rediscovery when IP changes

**Files to modify:**
- `cudy_client.py` - Add `get_clients()` method (exists in explorer, not in HA client)
- `config_flow.py` - Extract MAC/serial, update unique_id logic
- `coordinator.py` - Add rediscovery on connection failure
- `__init__.py` - Handle IP change recovery

**Reference:** Task #4, Project scope "Resilience to IP changes"

---

### 3. Options Flow
**Status:** ❌ Not implemented  
**Priority:** Medium (Nice to have for MVP)

**Missing:**
- Options flow for advanced settings
- Polling interval configuration
- SSL verify toggle (already in config, but should be in options)
- Update interval customization

**Files to create/modify:**
- `config_flow.py` - Add `async_get_options_flow()`

**Reference:** Task #5 in task list

---

### 4. Reboot Service Registration
**Status:** ✅ Complete  
**Priority:** Medium (MVP mentions service)

**Implemented:**
- ✅ Service registration: `cudy_scanner.reboot`
- ✅ Service schema with device_id
- ✅ Service handler in `__init__.py`
- ✅ Cooldown protection (60 seconds)

**Current state:**
- Reboot button works
- Reboot service works

**Files to modify:**
- `__init__.py` - Register service
- `const.py` - Add service constants

**Reference:** Task #9, Project scope mentions service

---

### 5. Uptime Sensor
**Status:** ✅ Complete  
**Priority:** Medium (MVP requirement)

**Implemented:**
- ✅ Uptime parsing from status HTML
- ✅ Uptime sensor entity
- ✅ Duration formatting (seconds)

**Current state:**
- Uptime sensor working
- Supports multiple time formats

**Files to modify:**
- `cudy_client.py` - Add uptime parsing in `_get_status_luci()`
- `sensor.py` - Add uptime sensor entity

**Reference:** Task #8, Project scope "uptime (if available)"

---

## 🟡 Important Missing Items

### 6. Rate Limiting & Global Semaphore
**Status:** ❌ Not implemented  
**Priority:** Medium (Stability requirement)

**Missing:**
- Global semaphore to prevent concurrent requests
- Rate limiting across all coordinators
- Jitter in coordinator intervals

**Current state:**
- No global rate limiting
- Fixed intervals, no jitter

**Files to modify:**
- `coordinator.py` - Add semaphore
- `const.py` - Add jitter configuration

**Reference:** Task #7, Learnings document mentions semaphore

---

### 7. Connected Clients Support
**Status:** ⚠️ Endpoint available, not used  
**Priority:** Low (Future enhancement)

**Missing:**
- `get_clients()` method in HA client (exists in explorer)
- Client list sensor/device tracker
- Mesh topology awareness

**Current state:**
- Explorer has `get_clients()` working
- HA client missing this method
- No entities for clients

**Files to modify:**
- `cudy_client.py` - Port `get_clients()` from explorer
- `coordinator.py` - Optionally fetch clients
- Future: `device_tracker.py` platform

**Reference:** Task #8 mentions clients, but out of scope for MVP

---

### 8. Device Registry Identifiers
**Status:** ⚠️ Partial (model only)  
**Priority:** Medium (For proper device tracking)

**Missing:**
- MAC address in device registry identifiers
- Serial number in device registry identifiers
- Proper device registry setup with stable identifiers

**Current state:**
- Device registry has model
- No MAC/serial identifiers

**Files to modify:**
- `sensor.py`, `binary_sensor.py`, `button.py` - Update DeviceInfo
- `coordinator.py` - Extract MAC/serial from clients endpoint

---

### 9. Error Handling Enhancements
**Status:** ⚠️ Basic implementation  
**Priority:** Medium

**Missing:**
- Exponential backoff in coordinator
- Better error messages for users
- Retry logic with jitter
- Connection failure recovery with rediscovery

**Current state:**
- Basic error handling exists
- No exponential backoff
- No automatic rediscovery

**Files to modify:**
- `coordinator.py` - Add backoff logic
- `cudy_client.py` - Enhance error handling

---

## 🟢 Documentation & Polish

### 10. README Update
**Status:** ⚠️ Basic README exists, needs update  
**Priority:** Low (But important for users)

**Missing:**
- Complete setup instructions
- Feature list
- Troubleshooting guide
- Known limitations
- Privacy notes
- Bug report guidance with diagnostics

**Files to modify:**
- `README.md` - Complete rewrite

---

### 11. Changelog
**Status:** ❌ Not created  
**Priority:** Low

**Missing:**
- `CHANGELOG.md` or `CHANGES.md`
- Version history
- Semantic versioning notes

**Files to create:**
- `CHANGELOG.md`

---

### 12. Testing Documentation
**Status:** ❌ Not created  
**Priority:** Medium

**Missing:**
- Manual test checklist
- Test scenarios
- Acceptance test plan

**Files to create:**
- `tests/` directory structure
- `TESTING.md` or test documentation

---

## 📋 Implementation Priority

### Phase 1: Critical MVP Features
1. **IP Change Resilience** - Extract MAC/serial, stable unique_id
2. **Discovery** - SSDP/UPnP basic implementation
3. **Uptime Sensor** - Parse and expose uptime
4. **Reboot Service** - Register service in addition to button

### Phase 2: Stability & Polish
5. **Rate Limiting** - Global semaphore, jitter
6. **Options Flow** - Advanced settings
7. **Error Handling** - Exponential backoff, better recovery
8. **Device Registry** - Proper identifiers

### Phase 3: Documentation
9. **README** - Complete documentation
10. **Changelog** - Version history
11. **Testing** - Test documentation

### Phase 4: Future Enhancements
12. **Connected Clients** - Device tracker support
13. **Mesh Topology** - Advanced features

---

## 🔍 Quick Reference: What Exists vs What's Missing

| Feature | Status | Notes |
|---------|--------|-------|
| Basic authentication | ✅ | Working |
| Status retrieval | ✅ | Model only, no uptime |
| Firmware sensor | ✅ | Working |
| WAN IP sensor | ✅ | Working |
| Online binary sensor | ✅ | Working |
| Reboot button | ✅ | Working |
| Config flow | ✅ | Basic, no discovery |
| Coordinator | ✅ | Basic, no rate limiting |
| Diagnostics | ✅ | Working |
| **Discovery** | ❌ | Not implemented |
| **IP resilience** | ⚠️ | Basic structure only |
| **Uptime sensor** | ❌ | Not implemented |
| **Reboot service** | ⚠️ | Button only, no service |
| **Options flow** | ❌ | Not implemented |
| **Rate limiting** | ❌ | Not implemented |
| **Clients support** | ⚠️ | Endpoint works, not integrated |
| **README** | ⚠️ | Basic, needs update |
| **Changelog** | ❌ | Not created |

---

## 🚀 Next Steps

1. **Immediate (Before testing):**
   - Add `get_clients()` to HA client
   - Extract MAC/serial for stable unique_id
   - Implement basic rediscovery

2. **Before MVP release:**
   - Discovery (SSDP basic)
   - Uptime sensor
   - Reboot service
   - README update

3. **Post-MVP:**
   - Options flow
   - Rate limiting
   - Connected clients
   - Full documentation

---

**Last Updated:** 2025-11-09  
**Review Status:** Ready for implementation prioritization

