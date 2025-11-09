# Cudy Scanner (HACS)

A Home Assistant custom integration to connect to Cudy routers on the local network, read configuration/status, and expose safe actions like reboot.

Status: Planning & scaffold (research-driven MVP).

## Goals
- Local-only connectivity to Cudy admin UI/API
- Entities for system status (uptime, firmware, WAN IP, clients)
- Services (e.g., `cudy_scanner.reboot`) with safety guards

## Install (dev)
- Copy this folder under `custom_components` via HACS custom repo or manual checkout (WIP)

## Roadmap (short)
- Config flow for host + credentials
- Coordinators for status polling
- Reboot service

See `experts/task-builder/tasks/cudy-scanner.hacs-plugin.20251107.v0.1.md` for the expert plan and gates.

