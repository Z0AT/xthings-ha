# Xthings Locks (ULTRALOQ Wi-Fi)

<p align="center">
  <img src="custom_components/xthings_lock/brand/icon.png" width="160" alt="ZOAT / Xthings Locks">
</p>

Unofficial [Home Assistant](https://www.home-assistant.io/) integration for **ULTRALOQ / U-tec** smart locks through the **Xthings Home** cloud.

This is **not** local LAN control. Wi-Fi Bolts do not expose a lock/unlock TCP API on your network. Status is polled from Xthings cloud. Lock and unlock use U-tec’s documented **OpenAPI**.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Validate](https://github.com/Z0AT/xthings-ha/actions/workflows/validate.yml/badge.svg)](https://github.com/Z0AT/xthings-ha/actions/workflows/validate.yml)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Z0AT&repository=xthings-ha&category=integration)

> Not affiliated with U-tec, ULTRALOQ, or Xthings. Use at your own risk.

## What you get

| Entity | What it does |
| --- | --- |
| `lock.<name>` | Lock and unlock over the lock’s Wi-Fi (OpenAPI) |
| `sensor.<name>_battery` | Cloud battery: Depleted / Replace / Low / Medium / High |
| `sensor.<name>_wi_fi_rssi` | Signal in dBm |
| `binary_sensor.<name>_wi_fi_remote` | Whether Wi-Fi remote is enabled in the Xthings app |

After a lock/unlock command the UI updates immediately (optimistic, ~20s), then the cloud poll (30s) or a DeviceState webhook confirms the real bolt state.

---

## Requirements

Before you install anything in Home Assistant:

1. The lock already works in the **Xthings Home** phone app.
2. **Wi-Fi remote** is enabled for that lock in the app (not BLE-only).
3. Home Assistant **2024.8** or newer.
4. You can log into the same Xthings account (email + password) that owns the lock.
5. For lock/unlock (not just status): an **OpenAPI** client in the Xthings app (steps below).
6. For OAuth and optional instant status: Home Assistant has an **external HTTPS URL**  
   (`Settings → System → Network → Home Assistant URL`). Nabu Casa, a reverse proxy, or a tunnel all work.

---

## 1. Create an Xthings OpenAPI client

Do this in the **Xthings Home** app (or U-tec OpenAPI page if your app version labels it that way).

1. Open **My Account → OpenAPI** (wording may be **Developer** / **Open API**).
2. Create a client. Copy the **Client ID** and **Client Secret**. Treat the secret like a password.
3. Set the redirect URI to **exactly**:

   ```
   https://my.home-assistant.io/redirect/oauth
   ```

4. Scope: **`openapi`**.
5. Save.

If OAuth later fails with a redirect mismatch, also add your instance callback:

```
https://YOUR-HOME-ASSISTANT-HOSTNAME/auth/external/callback
```

Keep the `my.home-assistant.io` URI. That is the one Home Assistant’s Application Credentials flow uses.

---

## 2. Install the integration

### HACS (recommended)

Once this repository is in the HACS default list you can search for **Xthings Locks**. Until then, add it as a custom repository:

1. [Open HACS and add this repository](https://my.home-assistant.io/redirect/hacs_repository/?owner=Z0AT&repository=xthings-ha&category=integration)  
   or: **HACS → Integrations → ⋮ → Custom repositories**
2. URL: `https://github.com/Z0AT/xthings-ha`
3. Type: **Integration**
4. **Download** / **Install** **Xthings Locks**
5. **Restart Home Assistant**

### Manual

Copy `custom_components/xthings_lock/` into `/config/custom_components/xthings_lock/` and restart.

---

## 3. Add Application Credentials in Home Assistant

Lock/unlock will not work until this is done.

1. **Settings → Devices & services**
2. Open **Application credentials** (three-dot menu on that page, or the link at the bottom)
3. **Add credential**
4. Application: **Xthings Locks**
5. Paste the OpenAPI **Client ID** and **Client Secret**
6. Save

---

## 4. Add the integration

1. **Settings → Devices & services → Add integration**
2. Search **Xthings Locks**
3. Sign in with the **same email and password** as the Xthings Home app  
   (this is how status, battery, and RSSI are read)
4. Home Assistant will send you to Xthings to **Authorize** OpenAPI  
   (this is how lock/unlock is sent)
5. Approve, then you should land back in Home Assistant with a device per lock

If you added the integration **before** Application Credentials:

- Status entities still appear
- Lock/unlock shows *OpenAPI is not linked yet*
- Add the credential (step 3), then **Add integration → Xthings Locks** again, sign in, and finish Authorize. It **merges onto the existing entry**; you do not get a second copy of the locks.

---

## 5. Optional: faster status (push)

Without extra work, lock state refreshes about every **30 seconds**.

If Home Assistant is reachable from the internet over HTTPS, the integration registers a webhook so keypad / app / fingerprint changes can show up without waiting for the poll.

Check **Settings → System → Network → Home Assistant URL** (the internet one). After a reload of the integration you should see `Registered Xthings push URL` in the logs. If that line is a warning instead, polling still works.

---

## Entities and automations

Each lock is a normal Home Assistant `lock` entity. Example:

```yaml
action: lock.unlock
target:
  entity_id: lock.front_door
```

```yaml
triggers:
  - trigger: state
    entity_id: lock.front_door
    to: unlocked
```

Names come from the Xthings app. Rename them in Home Assistant if you want.

---

## Troubleshooting

| What you see | What to do |
| --- | --- |
| Integration not in the Add list | Restart after HACS download. Confirm `custom_components/xthings_lock/` exists. |
| **Login failed** | Same email/password as the Xthings app. Not the OpenAPI client id. |
| **Could not reach Xthings cloud** | HA needs outbound HTTPS to `cloud.u-tec.com` / `oauth.u-tec.com` / `api.u-tec.com`. |
| **Add Xthings OpenAPI application credentials first** | Step 3 was skipped. Add the client id/secret, then add the integration again. |
| **OpenAPI is not linked yet** | OAuth never finished. Add integration again and complete Authorize. |
| Locks show **unavailable** | Confirm Wi-Fi remote is on in the app and the lock is online there. |
| Command works, UI lags | Normal for a few seconds. Enable an external URL if you want push. |
| OAuth redirect error | Redirect URI must be exactly `https://my.home-assistant.io/redirect/oauth`. Set HA’s external URL. |
| No devices | The Xthings account has no locks, or they are on a different email. |

Download **diagnostics** from the integration card if you open a GitHub issue. Credentials and tokens are stripped.

---

## Limitations

- Cloud-dependent. If Xthings or your WAN is down, commands fail the same way the phone app would.
- Not Bluetooth and not Z-Wave. Those are different hardware paths.
- Unofficial. U-tec can change the cloud API at any time.

---

## License

MIT for the integration code. See [LICENSE](LICENSE).

The ZOAT mark in `brand/` is the project logo (PNG, transparent). It is not a U-tec / ULTRALOQ trademark.
