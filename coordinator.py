"""Interrogation périodique de Printr."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PrintrAuthError, PrintrClient, PrintrError
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

type PrintrConfigEntry = ConfigEntry[PrintrCoordinator]


@dataclass
class PrintrData:
    status: dict[str, Any]
    presets: list[dict[str, Any]]
    shopping: list[dict[str, Any]]
    history: list[dict[str, Any]]


class PrintrCoordinator(DataUpdateCoordinator[PrintrData]):
    config_entry: PrintrConfigEntry

    def __init__(self, hass: HomeAssistant, entry: PrintrConfigEntry, client: PrintrClient) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self.client = client

    async def _async_update_data(self) -> PrintrData:
        try:
            status, presets, shopping, history = await asyncio.gather(
                self.client.status(),
                self.client.presets(),
                self.client.shopping(),
                self.client.history(),
            )
        except PrintrAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except PrintrError as err:
            raise UpdateFailed(str(err)) from err
        return PrintrData(status=status, presets=presets, shopping=shopping, history=history)
