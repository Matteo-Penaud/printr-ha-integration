"""Problème : la dernière impression a échoué (papier, imprimante débranchée…)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import PrintrConfigEntry
from .entity import PrintrEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: PrintrConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([PrintrProblem(entry.runtime_data, "problem")])


class PrintrProblem(PrintrEntity, BinarySensorEntity):
    _attr_translation_key = "problem"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    @property
    def is_on(self) -> bool:
        history = self.coordinator.data.history
        return bool(history) and not history[0].get("ok", True)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        history = self.coordinator.data.history
        if not history or history[0].get("ok", True):
            return None
        return {"errors": history[0].get("errors", [])}
