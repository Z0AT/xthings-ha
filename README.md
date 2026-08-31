# Xthings Locks (ULTRALOQ Wi-Fi)

Unofficial [Home Assistant](https://www.home-assistant.io/) integration for **ULTRALOQ / U-tec** smart locks through the **Xthings Home** cloud.

This is **not** local LAN control. The Bolt SE (and similar Wi-Fi models) do not expose a lock/unlock TCP API on your network. Status is polled from Xthings cloud; lock and unlock use U-tec’s documented **OpenAPI**.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Validate](https://github.com/Z0AT/xthings-ha/actions/workflows/validate.yml/badge.svg)](https://github.com/Z0AT/xthings-ha/actions/workflows/validate.yml)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Z0AT&repository=xthings-ha&category=integration)

> Not affiliated with U-tec, ULTRALOQ, or Xthings. Use at your own risk.

## What it does

- Discovers locks on your Xthings account
- `lock.*` entities with **lock** and **unlock** (OpenAPI over the lock’s Wi-Fi)
- Battery, Wi-Fi RSSI, Wi-Fi-remote diagnostic sensors
- Optimistic UI after a command, then a 30s cloud poll
- Optional **DeviceState** webhook so keypad / app changes can reach Home Assistant without waiting for the next poll

## Requirements

1. A U-tec lock that already works in the **Xthings Home** app over Wi-Fi remote
2. Home Assistant 2024.8 or newer (config entry + application credentials)
3. An Xthings **OpenAPI** client (in the app: **My Account → OpenAPI**)
4. Home Assistant reachable at an external URL if you want push status (Cloudflare Tunnel, Nabu Casa, etc.)

Redirect URI to register with Xthings OpenAPI:

```
https://my.home-assistant.io/redirect/oauth
```

## Install

### HACS (custom repository)

1. HACS → Integrations → custom repositories
2. URL: `https://github.com/Z0AT/xthings-ha`
3. Category: **Integration**
4. Download **Xthings Locks**, then restart Home Assistant

### Manual

Copy `custom_components/xthings_lock` into `/config/custom_components/xthings_lock` and restart.

## Setup

1. **Settings → Devices & services → Application credentials → Add credential**
   - Application: **Xthings Locks**
   - Client ID / Client secret from the Xthings OpenAPI page
2. **Add integration → Xthings Locks**
3. Sign in with the same email and password as the Xthings Home app
4. Complete the OpenAPI authorize step

Without OpenAPI credentials, the integration can still **read** lock state. Lock/unlock stays disabled until OAuth is linked (add the integration again after creating application credentials; it merges onto the existing entry).

## Entities

| Entity | Notes |
| --- | --- |
| `lock.<name>` | Lock / unlock via OpenAPI |
| `sensor.<name>_battery` | Cloud battery enum (Depleted / Replace / Low / Medium / High) |
| `sensor.<name>_wi_fi_rssi` | dBm |
| `binary_sensor.<name>_wi_fi_remote` | Whether Wi-Fi remote is enabled in the app |

## Limitations

- Cloud-dependent. If Xthings / WAN is down, commands fail the same way the phone app would.
- Not Bluetooth / Z-Wave. Those are separate hardware paths.
- Push updates need a public HTTPS webhook. Polling every 30 seconds still works without it.
- Unofficial. U-tec can change the cloud API at any time.

## HACS default store

This repo is structured for HACS (single integration under `custom_components/`, `hacs.json`, releases, hassfest + HACS validation). Submitting it to [hacs/default](https://github.com/hacs/default) is a later step after the GitHub repository is public and CI is green.

## License

MIT. See [LICENSE](LICENSE).
