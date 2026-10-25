"""Imprimer un message avec notify.send_message."""

from __future__ import annotations

from homeassistant.components.notify import NotifyEntity, NotifyEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import async_print, text_ticket
from .coordinator import PrintrConfigEntry
from .entity import PrintrEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: PrintrConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([PrintrNotify(entry.runtime_data, "notify")])


class PrintrNotify(PrintrEntity, NotifyEntity):
    _attr_translation_key = "ticket"
    _attr_supported_features = NotifyEntityFeature.TITLE

    async def async_send_message(self, message: str, title: str | None = None) -> None:
        await async_print(self.coordinator, text_ticket(message, title), title or "Home Assistant")
