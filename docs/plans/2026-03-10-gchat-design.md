# Google Chat Platform Module Design

## Overview

Add Google Chat as a new platform in bot-breacher, incorporating the capabilities from `gcp_audit5.py` into the existing platform module pattern.

## Authentication

- Uses Google service account JSON key files via `google-auth` + `google-api-python-client`
- Scope: `https://www.googleapis.com/auth/chat.bot`
- `create_service(path)` loads credentials, builds the Chat API v1 service object
- Token refresh handled automatically by the SDK

## Config

`config.yaml` entry:

```yaml
gchat:
  - name: "audit-bot"
    service_account_path: "/path/to/service_account.json"
```

`REQUIRED_FIELDS` in `core/config.py` adds `"gchat": ["name", "service_account_path"]`.

## Module Structure

```
bot_breacher/gchat/
├── __init__.py    # run_gchat_menu() — action dispatcher
├── auth.py        # create_service() — credential loading, API client
└── actions.py     # list_spaces, recon_space, send_text, send_card, card helpers
```

## Menu Actions

1. **List spaces** — discover all spaces the bot can access (read-only)
2. **Recon space** — metadata + member list for a specific space (read-only, console output)
3. **Send text message (targeted)** — plaintext to a single space
4. **Send text message (blast)** — plaintext to filtered spaces
5. **Send card message (targeted)** — CardV2 to a single space
6. **Send card message (blast)** — CardV2 to filtered spaces
7. **Back to main menu**

## Card Messages

Two sources for CardV2 payloads:

1. **Built-in "System Alert"** — hardcoded card structure from `gcp_audit5.py`, user provides alert text
2. **Custom templates** — CardV2 JSON files loaded from `google_cards/` directory (top-level, separate from Lark's `pretexts/`)

User chooses between "System Alert (built-in)" and available templates from `google_cards/`.

## Blast Mode Space Filtering

Before blasting, `questionary.checkbox()` prompts for space types to include:

- `SPACE` — named rooms/spaces
- `GROUP_CHAT` — group conversations
- `DIRECT_MESSAGE` — 1:1 DMs

All unchecked by default. User selects which to include.

## Actions API

```python
# auth.py
def create_service(service_account_path: str):
    """Load service account, build Chat API service. Returns service or None."""

# actions.py
def list_spaces(service) -> list[dict]:
    """List all accessible spaces. Prints via log_info. Returns space dicts."""

def recon_space(service, space_id: str) -> str | None:
    """Print space metadata + members via log_info. Returns display name."""

def send_text_message(service, space_id: str, text: str) -> tuple[bool, str]:
    """Send plaintext message. Returns (ok, detail)."""

def send_card_message(service, space_id: str, card_payload: dict) -> tuple[bool, str]:
    """Send CardV2 message. Returns (ok, detail)."""

def build_system_alert_card(space_id: str, alert_text: str) -> dict:
    """Construct the built-in System Alert CardV2 payload."""

def list_google_cards() -> list[str]:
    """List JSON filenames in google_cards/."""

def load_google_card(filename: str) -> dict | None:
    """Load and parse a CardV2 JSON file from google_cards/."""
```

## CLI Integration

- `pick_platform()` adds `"Google Chat"` before `"Exit"`
- `main()` adds `elif platform_key == "google chat":` branch
- Config key is `gchat`, display name is `"Google Chat"`

## Dependencies

Add to `requirements.txt`:

- `google-auth`
- `google-api-python-client`
