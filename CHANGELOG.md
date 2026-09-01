# Changelog

## 0.2.1

- ZOAT mark as integration icon/logo (PNG with real alpha)
- Drop `country` from `hacs.json` so HACS is not US-only
- Strip generator metadata from brand assets

## 0.2.0

- OpenAPI lock / unlock (`Uhome.Device` / `Command` / `st.lock`)
- Application credentials + OAuth2 config flow (merges onto an existing Xthings login)
- Optimistic lock state (~20s) plus optional DeviceState webhook
- 30s cloud poll fallback
- Battery, Wi-Fi RSSI, Wi-Fi-remote entities
- HACS packaging (`hacs.json`, GitHub Action validation, releases)

## 0.1.0

- Read-only cloud poll of lock metadata
