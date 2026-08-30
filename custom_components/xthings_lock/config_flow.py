from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import XthingsAuthError, XthingsClient
from .const import CONF_EMAIL, CONF_PASSWORD, DOMAIN

STEP_USER = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class XthingsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = XthingsClient(user_input[CONF_EMAIL], user_input[CONF_PASSWORD], session)
            try:
                devices = await client.async_get_devices()
            except XthingsAuthError:
                errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(user_input[CONF_EMAIL].lower())
                self._abort_if_unique_id_configured()
                title = f"Xthings ({len(devices)} lock{'s' if len(devices) != 1 else ''})"
                return self.async_create_entry(title=title, data=user_input)
        return self.async_show_form(step_id="user", data_schema=STEP_USER, errors=errors)
