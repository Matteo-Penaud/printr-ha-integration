"""Nouvelle version de Printr (signalée seulement : Printr ne s'installe pas tout seul)."""

from __future__ import annotations

from homeassistant.components.update import UpdateEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import PrintrConfigEntry
from .entity import PrintrEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: PrintrConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([PrintrUpdate(entry.runtime_data, "update")])


class PrintrUpdate(PrintrEntity, UpdateEntity):
    _attr_translation_key = "software"
    _attr_title = "Printr"

    @property
    def installed_version(self) -> str | None:
        return self.coordinator.data.status.get("version")

    @property
    def latest_version(self) -> str | None:
        update = self.coordinator.data.status.get("update")
        return update["version"].removeprefix("v") if update else self.installed_version

    @property
    def release_url(self) -> str | None:
        update = self.coordinator.data.status.get("update")
        return update["url"] if update else "https://github.com/XNinety9/Printr/releases"
