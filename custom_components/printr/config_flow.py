"""Configuration de Printr depuis l'interface."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_API_TOKEN, CONF_URL
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType

from .api import PrintrAuthError, PrintrClient, PrintrError
from .const import DOMAIN

TOKEN_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))


class PrintrConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def _check(self, url: str, token: str) -> str | None:
        """Renvoie la clé d'erreur du formulaire, ou None si Printr répond."""
        client = PrintrClient(async_get_clientsession(self.hass), url, token)
        try:
            await client.status(timeout=5)
        except PrintrAuthError:
            return "invalid_auth"
        except PrintrError:
            return "cannot_connect"
        return None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            url = user_input[CONF_URL].strip().rstrip("/")
            # Une tentative restée en attente (PC injoignable) ne doit pas bloquer la suivante.
            await self.async_set_unique_id(url, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            if not (error := await self._check(url, user_input[CONF_API_TOKEN])):
                return self.async_create_entry(
                    title="Printr", data={CONF_URL: url, CONF_API_TOKEN: user_input[CONF_API_TOKEN]}
                )
            errors["base"] = error
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema({vol.Required(CONF_URL): str, vol.Required(CONF_API_TOKEN): TOKEN_SELECTOR}),
                user_input or {CONF_URL: "http://"},
            ),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            if not (error := await self._check(entry.data[CONF_URL], user_input[CONF_API_TOKEN])):
                return self.async_update_reload_and_abort(entry, data_updates=user_input)
            errors["base"] = error
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_API_TOKEN): TOKEN_SELECTOR}),
            description_placeholders={"url": entry.data[CONF_URL]},
            errors=errors,
        )
