"""Constantes de l'intégration Printr."""

from datetime import timedelta

DOMAIN = "printr"

SCAN_INTERVAL = timedelta(seconds=60)

# Une impression peut attendre le réseau (actualités, météo) ou Claude (horoscope, mots fléchés).
PRINT_TIMEOUT = 180
REQUEST_TIMEOUT = 15

ATTR_CONFIG_ENTRY_ID = "config_entry_id"
ATTR_TICKET = "ticket"
ATTR_LABEL = "label"
ATTR_TEXT = "text"
ATTR_TITLE = "title"
ATTR_ITEMS = "items"
ATTR_ATTRIBUTES = "attributes"
ATTR_LAST_CHANGED = "last_changed"
ATTR_MESSAGE = "message"
ATTR_BLOCKS = "blocks"

SERVICE_PRINT_TICKET = "print_ticket"
SERVICE_PRINT_TEXT = "print_text"
SERVICE_PRINT_TODO = "print_todo"
SERVICE_PRINT_STATES = "print_states"
SERVICE_PREVIEW = "preview"
