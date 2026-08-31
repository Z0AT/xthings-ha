from __future__ import annotations

import logging
import secrets

from aiohttp.web import Request, Response, json_response
from homeassistant.components import webhook
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow, network
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import openapi_configure_notification
from .const import CONF_EMAIL, CONF_PASSWORD, DOMAIN, PLATFORMS, WEBHOOK_ID_PREFIX
from .coordinator import XthingsCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    oauth_session = None
    if entry.data.get("token"):
        implementation = await config_entry_oauth2_flow.async_get_config_entry_implementation(
            hass, entry
        )
        oauth_session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)
    coordinator = XthingsCoordinator(
        hass,
        session,
        entry.data[CONF_EMAIL],
        entry.data[CONF_PASSWORD],
        oauth_session,
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "webhook_id": None,
        "push_secret": None,
    }
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    if oauth_session:
        await _async_register_webhook(hass, entry, coordinator, oauth_session)
    return True


async def _async_register_webhook(hass, entry, coordinator, oauth_session) -> None:
    webhook_id = f"{WEBHOOK_ID_PREFIX}{entry.entry_id[:12]}"
    push_secret = secrets.token_urlsafe(24)

    async def _handle_webhook(
        hass: HomeAssistant, wh_id: str, request: Request
    ) -> Response:
        auth = request.headers.get("Authorization", "")
        incoming = auth.removeprefix("Bearer ").strip()
        stored = hass.data[DOMAIN][entry.entry_id].get("push_secret")
        if not stored or incoming != stored:
            return json_response({"success": False}, status=401)
        try:
            payload = await request.json()
        except Exception:
            return json_response({"success": False}, status=400)
        coordinator.apply_push(payload)
        return json_response({"success": True})

    webhook.async_register(
        hass, DOMAIN, "Xthings lock push", webhook_id, _handle_webhook
    )
    hass.data[DOMAIN][entry.entry_id]["webhook_id"] = webhook_id
    hass.data[DOMAIN][entry.entry_id]["push_secret"] = push_secret
    try:
        base = network.get_url(hass, prefer_external=True)
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning(
            "No external URL for Xthings push (set Home Assistant URL); polling still works: %s",
            err,
        )
        return
    url = f"{base.rstrip('/')}/api/webhook/{webhook_id}"
    try:
        await oauth_session.async_ensure_token_valid()
        token = oauth_session.token["access_token"]
        session = async_get_clientsession(hass)
        await openapi_configure_notification(session, token, url, push_secret)
        _LOGGER.info("Registered Xthings push URL")
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Xthings push registration failed (polling still works): %s", err)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id) or {}
    webhook_id = data.get("webhook_id")
    if webhook_id:
        webhook.async_unregister(hass, webhook_id)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
