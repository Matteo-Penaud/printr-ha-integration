"""Un bouton par ticket enregistré (preset) partagé dans Printr."""

from __future__ import annotations

from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import PrintrError
from .const import DOMAIN, PRINT_TIMEOUT
from .coordinator import PrintrConfigEntry, PrintrCoordinator
from .entity import PrintrEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: PrintrConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    known: set[str] = set()

    @callback
    def sync() -> None:
        current = {p["id"] for p in coordinator.data.presets}
        if new := current - known:
            async_add_entities(PrintrPresetButton(coordinator, pid) for pid in sorted(new))
        # Preset supprimé (ou plus partagé) dans Printr : on retire son bouton.
        registry = er.async_get(hass)
        for pid in known - current:
            if entity_id := registry.async_get_entity_id("button", DOMAIN, f"{entry.entry_id}_preset_{pid}"):
                registry.async_remove(entity_id)
        known.clear()
        known.update(current)

    sync()
    entry.async_on_unload(coordinator.async_add_listener(sync))


class PrintrPresetButton(PrintrEntity, ButtonEntity):
    _attr_translation_key = "preset"

    def __init__(self, coordinator: PrintrCoordinator, preset_id: str) -> None:
        super().__init__(coordinator, f"preset_{preset_id}")
        self._preset_id = preset_id

    @property
    def _preset(self) -> dict[str, Any] | None:
        return next((p for p in self.coordinator.data.presets if p["id"] == self._preset_id), None)

    @property
    def name(self) -> str | None:
        preset = self._preset
        if preset is None:
            return None
        return f"{preset.get('icon', '')} {preset['name']}".strip()

    @property
    def available(self) -> bool:
        return super().available and self._preset is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        preset = self._preset
        if preset is None:
            return None
        owner = preset.get("owner") or {}
        return {
            "preset_id": self._preset_id,
            "owner": owner.get("name"),
            "schedules": preset.get("schedules", []),
        }

    async def async_press(self) -> None:
        try:
            errors = await self.coordinator.client.print_preset(self._preset_id, PRINT_TIMEOUT)
        except PrintrError as err:
            raise HomeAssistantError(f"Impression refusée par Printr : {err}") from err
        if errors:
            raise HomeAssistantError(f"Ticket imprimé, blocs en échec : {'; '.join(errors)}")
        await self.coordinator.async_request_refresh()
