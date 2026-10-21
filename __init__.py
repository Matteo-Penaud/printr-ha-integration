"""Intégration Home Assistant pour Printr, l'imprimante à tickets familiale."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_ENTITY_ID, CONF_API_TOKEN, CONF_URL, Platform
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import PrintrClient, PrintrError
from .const import (
    ATTR_ATTRIBUTES,
    ATTR_BLOCKS,
    ATTR_CONFIG_ENTRY_ID,
    ATTR_ITEMS,
    ATTR_LABEL,
    ATTR_LAST_CHANGED,
    ATTR_MESSAGE,
    ATTR_TEXT,
    ATTR_TICKET,
    ATTR_TITLE,
    DOMAIN,
    PRINT_TIMEOUT,
    SERVICE_PREVIEW,
    SERVICE_PRINT_STATES,
    SERVICE_PRINT_TEXT,
    SERVICE_PRINT_TICKET,
    SERVICE_PRINT_TODO,
)
from .coordinator import PrintrConfigEntry, PrintrCoordinator
from .states import states_ticket

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NOTIFY,
    Platform.SENSOR,
    Platform.TODO,
    Platform.UPDATE,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

ENTRY_SCHEMA = {vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string}

PRINT_TICKET_SCHEMA = vol.Schema(
    {
        **ENTRY_SCHEMA,
        vol.Required(ATTR_TICKET): dict,
        vol.Optional(ATTR_LABEL): cv.string,
    }
)
PRINT_TEXT_SCHEMA = vol.Schema(
    {
        **ENTRY_SCHEMA,
        vol.Required(ATTR_TEXT): cv.string,
        vol.Optional(ATTR_TITLE): cv.string,
    }
)
PRINT_TODO_SCHEMA = vol.Schema(
    {
        **ENTRY_SCHEMA,
        vol.Required(ATTR_ITEMS): vol.All(cv.ensure_list, [cv.string], vol.Length(min=1)),
        vol.Optional(ATTR_TITLE): cv.string,
    }
)
PRINT_STATES_SCHEMA = vol.Schema(
    {
        **ENTRY_SCHEMA,
        vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
        vol.Optional(ATTR_TITLE): cv.string,
        vol.Optional(ATTR_ATTRIBUTES, default=False): cv.boolean,
        vol.Optional(ATTR_LAST_CHANGED, default=False): cv.boolean,
        vol.Optional(ATTR_MESSAGE): cv.string,
        vol.Optional(ATTR_BLOCKS, default=list): vol.All(cv.ensure_list, [dict]),
        vol.Optional(ATTR_LABEL): cv.string,
    }
)
PREVIEW_SCHEMA = vol.Schema({**ENTRY_SCHEMA, vol.Required(ATTR_TICKET): dict})


def text_ticket(text: str, title: str | None = None) -> dict[str, Any]:
    """Ticket simple : un titre facultatif puis le texte."""
    blocks: list[dict[str, Any]] = []
    if title:
        blocks.append({"type": "title", "text": title})
    blocks.append({"type": "text", "text": text})
    return {"cut": True, "blocks": blocks}


async def async_print(coordinator: PrintrCoordinator, ticket: dict[str, Any], label: str | None) -> list[str]:
    """Imprime, signale les blocs en échec et rafraîchit l'historique."""
    try:
        errors = await coordinator.client.print_ticket(ticket, label, PRINT_TIMEOUT)
    except PrintrError as err:
        raise HomeAssistantError(f"Impression refusée par Printr : {err}") from err
    if errors:
        _LOGGER.warning("Ticket imprimé, blocs en échec : %s", "; ".join(errors))
    await coordinator.async_request_refresh()
    return errors


def _coordinator(hass: HomeAssistant, call: ServiceCall) -> PrintrCoordinator:
    """Instance visée par l'action ; facultative quand il n'y en a qu'une."""
    loaded = [e for e in hass.config_entries.async_entries(DOMAIN) if e.state is ConfigEntryState.LOADED]
    if entry_id := call.data.get(ATTR_CONFIG_ENTRY_ID):
        loaded = [e for e in loaded if e.entry_id == entry_id]
    elif len(loaded) > 1:
        raise ServiceValidationError("Plusieurs instances Printr : préciser config_entry_id")
    if not loaded:
        raise ServiceValidationError("Instance Printr inconnue ou indisponible")
    entry: PrintrConfigEntry = loaded[0]
    return entry.runtime_data


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Enregistre les actions, communes à toutes les instances."""

    async def print_ticket(call: ServiceCall) -> ServiceResponse:
        errors = await async_print(_coordinator(hass, call), call.data[ATTR_TICKET], call.data.get(ATTR_LABEL))
        return {"errors": errors}

    async def print_text(call: ServiceCall) -> ServiceResponse:
        ticket = text_ticket(call.data[ATTR_TEXT], call.data.get(ATTR_TITLE))
        errors = await async_print(_coordinator(hass, call), ticket, call.data.get(ATTR_TITLE) or "Home Assistant")
        return {"errors": errors}

    async def print_todo(call: ServiceCall) -> ServiceResponse:
        title = call.data.get(ATTR_TITLE)
        todo: dict[str, Any] = {"type": "todo", "items": call.data[ATTR_ITEMS]}
        if title:
            todo["title"] = title
        ticket = {"cut": True, "blocks": [{"type": "date"}, todo]}
        errors = await async_print(_coordinator(hass, call), ticket, title or "Liste à faire")
        return {"errors": errors}

    async def print_states(call: ServiceCall) -> ServiceResponse:
        title = call.data.get(ATTR_TITLE)
        ticket = states_ticket(
            hass,
            call.data[ATTR_ENTITY_ID],
            title,
            call.data[ATTR_ATTRIBUTES],
            call.data[ATTR_LAST_CHANGED],
            call.data.get(ATTR_MESSAGE),
            call.data[ATTR_BLOCKS],
        )
        label = call.data.get(ATTR_LABEL) or title or "États Home Assistant"
        errors = await async_print(_coordinator(hass, call), ticket, label)
        return {"errors": errors}

    async def preview(call: ServiceCall) -> ServiceResponse:
        try:
            text = await _coordinator(hass, call).client.preview(call.data[ATTR_TICKET], PRINT_TIMEOUT)
        except PrintrError as err:
            raise HomeAssistantError(f"Aperçu refusé par Printr : {err}") from err
        return {"preview": text}

    for name, handler, schema in (
        (SERVICE_PRINT_TICKET, print_ticket, PRINT_TICKET_SCHEMA),
        (SERVICE_PRINT_TEXT, print_text, PRINT_TEXT_SCHEMA),
        (SERVICE_PRINT_TODO, print_todo, PRINT_TODO_SCHEMA),
        (SERVICE_PRINT_STATES, print_states, PRINT_STATES_SCHEMA),
    ):
        hass.services.async_register(DOMAIN, name, handler, schema, supports_response=SupportsResponse.OPTIONAL)
    hass.services.async_register(
        DOMAIN, SERVICE_PREVIEW, preview, PREVIEW_SCHEMA, supports_response=SupportsResponse.ONLY
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: PrintrConfigEntry) -> bool:
    client = PrintrClient(async_get_clientsession(hass), entry.data[CONF_URL], entry.data[CONF_API_TOKEN])
    coordinator = PrintrCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: PrintrConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
