# Xthings / Ultraloq Wi-Fi (cloud) for Home Assistant

Private research integration for **your** ULTRALOQ Bolt locks.

This is **not** local LAN control. The Bolts do not listen on any TCP port.
Wi-Fi remote in the Xthings app is:

```
phone  --MQTTS-->  a30xqtffg389ek-ats.iot.us-west-2.amazonaws.com:8883
                   topics: utec/lock/BOLT/<ble-uuid>/lock|unlock|connect|whatever
```

The app authenticates to AWS IoT with an **embedded client certificate** (`ProtectorLib` PKCS12), then publishes. Extracting and redistributing that cert is out of scope for this repo.

What this integration **does** today:

- Logs into `cloud.u-tec.com` with the same email/password as Xthings Home
- Polls `device/list` / `device/get`
- Exposes lock **state**, battery, Wi-Fi RSSI, `wifi_remote` flag

Lock/unlock buttons are **not** wired. Use the Xthings app or the BLE integration until MQTT is implemented with a user-held cert (not shipped here).

## Install

Copy `custom_components/xthings_lock` into `/config/custom_components/xthings_lock`, restart Home Assistant, then **Settings → Devices & services → Add → Xthings Locks**.

Do not commit `~/.secrets/xthings.env` or APKs.
