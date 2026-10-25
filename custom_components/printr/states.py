"""Mise en page des états d'entités Home Assistant sur un ticket."""

from __future__ import annotations

import textwrap
from typing import Any

from homeassistant.const import ATTR_DEVICE_CLASS, ATTR_UNIT_OF_MEASUREMENT, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.translation import async_translate_state
from homeassistant.util import dt as dt_util

# Largeur d'une ligne en police normale (`doc.rs` de Printr) et en petite police.
COLUMNS = 42
COLUMNS_SMALL = 56

# Attributs techniques, sans intérêt sur papier.
HIDDEN_ATTRIBUTES = {
    "friendly_name",
    "unit_of_measurement",
    "device_class",
    "state_class",
    "icon",
    "entity_picture",
    "supported_features",
    "attribution",
    "assumed_state",
    "restored",
    "editable",
    "id",
    "options",
}

UNAVAILABLE = {STATE_UNAVAILABLE: "indisponible", STATE_UNKNOWN: "inconnu"}


def _decimal(value: float, precision: int | None, language: str) -> str:
    text = f"{value:.{precision}f}" if precision is not None else f"{value:g}"
    return text.replace(".", ",") if language.startswith("fr") else text


def _value(hass: HomeAssistant, state: State, entry: er.RegistryEntry | None) -> str:
    """Valeur lisible : état traduit, nombre arrondi avec son unité, date locale."""
    if state.state in UNAVAILABLE:
        return UNAVAILABLE[state.state]
    device_class = state.attributes.get(ATTR_DEVICE_CLASS)
    if device_class == "timestamp" and (when := dt_util.parse_datetime(state.state)):
        return dt_util.as_local(when).strftime("%d/%m %H:%M")
    unit = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
    try:
        number = float(state.state)
    except ValueError:
        number = None
    if number is not None and state.domain in ("sensor", "number", "input_number"):
        options = entry.options.get("sensor", {}) if entry else {}
        precision = options.get("display_precision", options.get("suggested_display_precision"))
        text = _decimal(number, precision, hass.config.language)
    else:
        text = async_translate_state(
            hass,
            state.state,
            state.domain,
            entry.platform if entry else None,
            entry.translation_key if entry else None,
            device_class,
        )
    return f"{text} {unit}" if unit else text


def _line(name: str, value: str, width: int = COLUMNS) -> str:
    """« Nom ....... valeur », la valeur toujours alignée à droite.

    Printr retire les espaces en début de ligne : les points servent aussi à aligner quand le
    nom est trop long et passe sur plusieurs lignes.
    """
    lines = textwrap.wrap(name, width) or [""]
    last = lines.pop()
    if width - len(last) - len(value) - 2 < 2:
        lines.append(last)
        last = ""
    dots = width - len(last) - len(value) - (2 if last else 1)
    lines.append(f"{last} {'.' * dots} {value}" if last else f"{'.' * dots} {value}")
    return "\n".join(lines)


def states_ticket(
    hass: HomeAssistant,
    entity_ids: list[str],
    title: str | None,
    attributes: bool,
    last_changed: bool,
    message: str | None = None,
    extra_blocks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    registry = er.async_get(hass)
    now = dt_util.now()
    blocks: list[dict[str, Any]] = [
        {"type": "title", "text": title or "Home Assistant"},
        {"type": "text", "text": now.strftime("%d/%m/%Y %H:%M"), "align": "center", "small": True},
        {"type": "separator"},
    ]
    for entity_id in entity_ids:
        state = hass.states.get(entity_id)
        if state is None:
            blocks.append({"type": "text", "text": _line(entity_id, "introuvable")})
            continue
        value = _value(hass, state, registry.async_get(entity_id))
        blocks.append({"type": "text", "text": _line(state.name, value)})
        details: list[str] = []
        if last_changed:
            changed = dt_util.as_local(state.last_changed)
            when = changed.strftime("%H:%M") if changed.date() == now.date() else changed.strftime("%d/%m %H:%M")
            details.append(_line("· depuis", when, COLUMNS_SMALL))
        if attributes:
            details.extend(
                _line(f"· {key}", str(val), COLUMNS_SMALL)
                for key, val in state.attributes.items()
                if key not in HIDDEN_ATTRIBUTES and val not in (None, "", [], {})
            )
        if details:
            blocks.append({"type": "text", "text": "\n".join(details), "small": True})
    if message:
        blocks += [{"type": "separator"}, {"type": "text", "text": message}]
    if extra_blocks:
        # Les blocs Printr (météo, citation…) gardent leur espacement habituel.
        blocks += [{"type": "feed"}, *extra_blocks]
    return {"cut": True, "spacing": 0, "blocks": blocks}
