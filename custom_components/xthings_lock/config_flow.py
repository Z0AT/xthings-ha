from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import SOURCE_REAUTH
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import XthingsAuthError, XthingsClient
from .const import CONF_EMAIL, CONF_PASSWORD, DOMAIN, OAUTH_SCOPE

_LOGGER = logging.getLogger(__name__)

STEP_ACCOUNT = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class XthingsOAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Xthings account login, then optional OpenAPI OAuth for lock/unlock."""

    DOMAIN = DOMAIN
    VERSION = 1

    def __init__(self) -> None:
        super().__init__()
        self._email: str | None = None
        self._password: str | None = None
        self._device_count: int = 0

    @property
    def logger(self) -> logging.Logger:
        return _LOGGER

    @property
    def extra_authorize_data(self) -> dict[str, str]:
        return {"scope": OAUTH_SCOPE}

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Start with the Xthings account (email/password)."""
        return await self.async_step_account(user_input)

    async def async_step_reauth(self, entry_data: dict[str, Any]):
        self._email = entry_data.get(CONF_EMAIL)
        self._password = entry_data.get(CONF_PASSWORD)
        return await self.async_step_account()

    async def async_step_account(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = XthingsClient(
                user_input[CONF_EMAIL], user_input[CONF_PASSWORD], session
            )
            try:
                devices = await client.async_get_devices()
            except XthingsAuthError:
                errors["base"] = "invalid_auth"
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"
            else:
                self._email = user_input[CONF_EMAIL]
                self._password = user_input[CONF_PASSWORD]
                self._device_count = len(devices)
                await self.async_set_unique_id(self._email.lower())
                implementations = (
                    await config_entry_oauth2_flow.async_get_implementations(
                        self.hass, self.DOMAIN
                    )
                )
                if not implementations:
                    if self.source == SOURCE_REAUTH:
                        return self._async_update_reauth_entry()
                    self._abort_if_unique_id_configured()
                    return self._async_create_account_entry()
                return await self.async_step_pick_implementation()
        suggested: dict[str, Any] = {}
        if self.source == SOURCE_REAUTH and self._email:
            suggested[CONF_EMAIL] = self._email
        return self.async_show_form(
            step_id="account",
            data_schema=self.add_suggested_values_to_schema(STEP_ACCOUNT, suggested),
            errors=errors,
        )

    def _async_create_account_entry(self):
        n = self._device_count
        title = f"Xthings ({n} lock{'s' if n != 1 else ''})"
        return self.async_create_entry(
            title=title,
            data={CONF_EMAIL: self._email, CONF_PASSWORD: self._password},
        )

    def _async_update_reauth_entry(self):
        """Store new credentials on the entry that started reauthentication."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        if entry is None:
            return self.async_abort(reason="reauth_failed")
        other = self.hass.config_entries.async_entry_for_domain_unique_id(
            DOMAIN, (self._email or "").lower()
        )
        if other is not None and other.entry_id != entry.entry_id:
            return self.async_abort(reason="already_configured")
        return self.async_update_reload_and_abort(
            entry,
            unique_id=(self._email or "").lower() or entry.unique_id,
            data={
                **entry.data,
                CONF_EMAIL: self._email,
                CONF_PASSWORD: self._password,
            },
        )

    async def async_oauth_create_entry(self, data: dict[str, Any]):
        combined = dict(data)
        if self._email:
            combined[CONF_EMAIL] = self._email
            combined[CONF_PASSWORD] = self._password
        email = (combined.get(CONF_EMAIL) or "").lower()
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            existing_email = str(entry.data.get(CONF_EMAIL, "")).lower()
            if email and existing_email == email:
                self.hass.config_entries.async_update_entry(
                    entry, data={**entry.data, **combined}
                )
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="oauth_linked")
        n = self._device_count
        title = f"Xthings ({n} lock{'s' if n != 1 else ''})" if n else "Xthings"
        return self.async_create_entry(title=title, data=combined)
