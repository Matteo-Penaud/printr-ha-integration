"""Dernière impression et nombre de tickets du jour."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .coordinator import PrintrConfigEntry
from .entity import PrintrEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: PrintrConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities([LastPrintSensor(coordinator, "last_print"), PrintsTodaySensor(coordinator, "prints_today")])


def _at(entry: dict[str, Any]) -> datetime | None:
    return dt_util.parse_datetime(entry["at"]) if entry.get("at") else None


class LastPrintSensor(PrintrEntity, SensorEntity):
    _attr_translation_key = "last_print"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self) -> datetime | None:
        history = self.coordinator.data.history
        return _at(history[0]) if history else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        history = self.coordinator.data.history
        if not history:
            return None
        last = history[0]
        return {
            "label": last.get("label"),
            "by": last.get("by"),
            "ok": last.get("ok"),
            "errors": last.get("errors", []),
            "blocks": last.get("blocks", []),
            "paper_mm": last.get("paper_mm"),
        }


class PrintsTodaySensor(PrintrEntity, SensorEntity):
    _attr_translation_key = "prints_today"
    _attr_native_unit_of_measurement = "tickets"

    @property
    def native_value(self) -> int:
        today = dt_util.now().date()
        return sum(
            1
            for e in self.coordinator.data.history
            if e.get("ok") and (at := _at(e)) and dt_util.as_local(at).date() == today
        )
