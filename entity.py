"""Entité de base Printr."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PrintrCoordinator


class PrintrEntity(CoordinatorEntity[PrintrCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: PrintrCoordinator, key: str) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        status = coordinator.data.status
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Printr",
            manufacturer="XNinety9",
            model=status.get("printer") or "Printr",
            sw_version=status.get("version"),
            configuration_url=coordinator.client.url,
        )
