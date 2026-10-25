# Printr for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
[![Validate](https://github.com/Matteo-Penaud/printr-ha-integration/actions/workflows/validate.yml/badge.svg)](https://github.com/Matteo-Penaud/printr-ha-integration/actions/workflows/validate.yml)

Home Assistant integration for [Printr](https://github.com/XNinety9/Printr), the family receipt printer.
It talks to the `printr serve` HTTP API over the local network.

## Features

- **Notify entity**: print a ticket from any automation with `notify.send_message`.
- **Buttons**: one button per Printr preset.
- **Shopping list**: a to-do entity synced with Printr's shopping list.
- **Sensors**: last print time, tickets printed today, print failure (problem binary sensor).
- **Update entity**: shows the Printr software version.
- **Actions**: `printr.print_ticket`, `printr.print_text`, `printr.print_todo`, `printr.print_states` and `printr.preview`.

## Installation

### HACS (recommended)

1. In HACS, open the menu ⋮ → **Custom repositories**.
2. Add `https://github.com/Matteo-Penaud/printr-ha-integration` with the category **Integration**.
3. Search for **Printr**, install it, then restart Home Assistant.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Matteo-Penaud&repository=printr-ha-integration&category=integration)

### Manual

Copy `custom_components/printr` into the `custom_components` folder of your Home Assistant configuration, then restart.

## Configuration

**Settings → Devices & services → Add integration → Printr**, then enter:

- **URL**: address of the `printr serve` server, e.g. `http://192.168.1.50:8080`.
- **Token**: the script token, `PRINTR_TOKEN` in `/etc/printr.env` on the Printr host.

## Example

```yaml
action: printr.print_ticket
data:
  label: Morning ticket
  ticket:
    cut: true
    blocks:
      - type: title
        text: Good morning!
      - type: weather
        location: Paris
```

## License

[GPL-3.0](LICENSE)
