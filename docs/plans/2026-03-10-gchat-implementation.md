# Google Chat Platform Module Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Google Chat as a platform in bot-breacher with space discovery, recon, and message sending (text + CardV2).

**Architecture:** New `bot_breacher/gchat/` module following the existing auth/actions/menu pattern. Service account credentials via `google-auth`, API calls via `google-api-python-client`. Card templates loaded from `google_cards/` directory.

**Tech Stack:** `google-auth==2.49.0`, `google-api-python-client==2.192.0`, existing `questionary`/`rich` TUI

---

### Task 1: Add dependencies

**Files:**
- Modify: `requirements.txt`

**Step 1: Add google-auth and google-api-python-client to requirements.txt**

Append to the end of `requirements.txt`:

```
google-auth==2.49.0
google-api-python-client==2.192.0
```

**Step 2: Install dependencies**

Run: `pip install -r requirements.txt`
Expected: All packages install successfully

**Step 3: Commit**

```bash
git add requirements.txt
git commit -m "feat(gchat): add google-auth and google-api-python-client dependencies"
```

---

### Task 2: Create auth module

**Files:**
- Create: `bot_breacher/gchat/__init__.py`
- Create: `bot_breacher/gchat/auth.py`

**Step 1: Create empty `__init__.py`**

```python
"""Google Chat platform menu and action dispatcher."""
```

Just the docstring for now — the menu function is added in Task 5.

**Step 2: Create `auth.py`**

```python
"""Google Chat service account authentication."""

import os

from google.oauth2 import service_account
from googleapiclient.discovery import build

from bot_breacher.core.logger import log_info

SCOPES = ["https://www.googleapis.com/auth/chat.bot"]


def create_service(service_account_path):
    """Load service account credentials and build Chat API service.

    Args:
        service_account_path: Path to the service account JSON key file.

    Returns:
        Google Chat API service object, or None on failure.
    """
    if not os.path.exists(service_account_path):
        log_info(
            f"[red]Service account file not found: "
            f"{service_account_path}[/red]"
        )
        return None

    try:
        creds = service_account.Credentials.from_service_account_file(
            service_account_path, scopes=SCOPES
        )
        service = build("chat", "v1", credentials=creds)
        log_info("[green]Google Chat service authenticated[/green]")
        return service
    except Exception as e:
        log_info(f"[red]Google Chat auth failed: {e}[/red]")
        return None
```

**Step 3: Commit**

```bash
git add bot_breacher/gchat/__init__.py bot_breacher/gchat/auth.py
git commit -m "feat(gchat): add auth module with service account credential loading"
```

---

### Task 3: Create actions module

**Files:**
- Create: `bot_breacher/gchat/actions.py`

**Step 1: Create `actions.py`**

```python
"""Google Chat actions: list spaces, recon, send text, send cards."""

import json
import os

from bot_breacher.core.logger import log_info

GOOGLE_CARDS_DIR = "google_cards/"


def list_spaces(service):
    """List all spaces the bot can access.

    Returns:
        List of space dicts, or empty list on failure.
    """
    try:
        result = service.spaces().list().execute()
        spaces = result.get("spaces", [])
        if not spaces:
            log_info("[yellow]No accessible spaces found.[/yellow]")
            return []
        log_info(f"[cyan]Found {len(spaces)} space(s):[/cyan]")
        for s in spaces:
            s_type = s.get("spaceType", "UNKNOWN")
            s_name = s.get("displayName", "DM")
            log_info(f"  {s['name']} | {s_name} | {s_type}")
        return spaces
    except Exception as e:
        log_info(f"[red]Failed to list spaces: {e}[/red]")
        return []


def recon_space(service, space_id):
    """Retrieve metadata and member list for a space.

    Args:
        service: Google Chat API service object.
        space_id: Space resource name (e.g. "spaces/ABC123").

    Returns:
        Display name string, or None on failure.
    """
    try:
        space_info = service.spaces().get(name=space_id).execute()
        s_type = space_info.get("spaceType", "UNKNOWN")
        s_display = space_info.get(
            "displayName", "Direct Message (1:1)"
        )

        log_info(f"[cyan]Space:[/cyan] {s_display}")
        log_info(f"[cyan]Type:[/cyan] {s_type}")

        members_res = (
            service.spaces()
            .members()
            .list(parent=space_id)
            .execute()
        )
        members = members_res.get("memberships", [])

        log_info(f"[cyan]Members ({len(members)}):[/cyan]")
        for m in members:
            user = m.get("member", {})
            name = user.get("displayName", "Unknown")
            user_type = user.get("type", "UNKNOWN")
            log_info(f"  - {name} [{user_type}]")

        return s_display
    except Exception as e:
        log_info(f"[red]Recon failed for {space_id}: {e}[/red]")
        return None


def send_text_message(service, space_id, text):
    """Send a plaintext message to a space.

    Returns:
        (ok, detail) tuple.
    """
    try:
        service.spaces().messages().create(
            parent=space_id, body={"text": text}
        ).execute()
        return True, f"Delivered to {space_id}"
    except Exception as e:
        return False, str(e)


def send_card_message(service, space_id, card_payload):
    """Send a CardV2 message to a space.

    Args:
        service: Google Chat API service object.
        space_id: Space resource name.
        card_payload: Dict with "cardsV2" key.

    Returns:
        (ok, detail) tuple.
    """
    try:
        service.spaces().messages().create(
            parent=space_id, body=card_payload
        ).execute()
        return True, f"Card delivered to {space_id}"
    except Exception as e:
        return False, str(e)


def build_system_alert_card(space_id, alert_text):
    """Construct the built-in System Alert CardV2 payload."""
    icon_url = (
        "https://developers.google.com/chat/images/"
        "chat-product-icon.png"
    )
    return {
        "cardsV2": [
            {
                "cardId": "system_alert_01",
                "card": {
                    "header": {
                        "title": "SYSTEM SECURITY ALERT",
                        "subtitle": "See below for details",
                        "imageUrl": icon_url,
                        "imageType": "CIRCLE",
                    },
                    "sections": [
                        {
                            "header": "Audit Findings",
                            "collapsible": False,
                            "uncollapsibleWidgetsCount": 1,
                            "widgets": [
                                {
                                    "textParagraph": {
                                        "text": (
                                            "<b>Warning:</b> "
                                            "Unverified application "
                                            "presence detected in "
                                            "this space. Proceed "
                                            "with caution when "
                                            "sharing credentials "
                                            "and raise security "
                                            "on-call ticket if "
                                            "compromised.<br><br>"
                                            f"{alert_text}"
                                        )
                                    }
                                },
                                {
                                    "decoratedText": {
                                        "topLabel": "Space ID",
                                        "text": space_id,
                                        "bottomLabel": (
                                            "Verify with "
                                            "Admin Console"
                                        ),
                                        "wrapText": True,
                                    }
                                },
                            ],
                        }
                    ],
                },
            }
        ]
    }


def list_google_cards():
    """List available CardV2 JSON files in google_cards/.

    Returns:
        List of filenames, or empty list.
    """
    if not os.path.isdir(GOOGLE_CARDS_DIR):
        return []
    return [
        f
        for f in os.listdir(GOOGLE_CARDS_DIR)
        if os.path.isfile(os.path.join(GOOGLE_CARDS_DIR, f))
        and f.endswith(".json")
    ]


def load_google_card(filename):
    """Load a CardV2 JSON template from google_cards/.

    Returns:
        Parsed dict, or None on failure.
    """
    path = os.path.join(GOOGLE_CARDS_DIR, filename)
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        log_info(f"[red]Failed to load card {filename}: {e}[/red]")
        return None
```

**Step 2: Commit**

```bash
git add bot_breacher/gchat/actions.py
git commit -m "feat(gchat): add actions module with space ops and messaging"
```

---

### Task 4: Create example card template

**Files:**
- Create: `google_cards/system-alert-example.json`

**Step 1: Create `google_cards/` directory and example card**

```json
{
    "cardsV2": [
        {
            "cardId": "system_alert_example",
            "card": {
                "header": {
                    "title": "SYSTEM SECURITY ALERT",
                    "subtitle": "See below for details",
                    "imageUrl": "https://developers.google.com/chat/images/chat-product-icon.png",
                    "imageType": "CIRCLE"
                },
                "sections": [
                    {
                        "header": "Alert Details",
                        "collapsible": false,
                        "widgets": [
                            {
                                "textParagraph": {
                                    "text": "<b>Notice:</b> This is an example system alert card template. Edit this file to customize for your engagement."
                                }
                            }
                        ]
                    }
                ]
            }
        }
    ]
}
```

**Step 2: Commit**

```bash
git add google_cards/system-alert-example.json
git commit -m "feat(gchat): add example CardV2 template in google_cards/"
```

---

### Task 5: Create menu module

**Files:**
- Modify: `bot_breacher/gchat/__init__.py`

**Step 1: Replace `__init__.py` with the full menu dispatcher**

```python
"""Google Chat platform menu and action dispatcher."""

import questionary

from bot_breacher.core.cli import confirm_send
from bot_breacher.core.logger import log_info, log_result
from bot_breacher.gchat.actions import (
    build_system_alert_card,
    list_google_cards,
    list_spaces,
    load_google_card,
    recon_space,
    send_card_message,
    send_text_message,
)
from bot_breacher.gchat.auth import create_service

SPACE_TYPES = ["SPACE", "GROUP_CHAT", "DIRECT_MESSAGE"]


def _pick_space_id():
    """Prompt for a space ID."""
    return questionary.text(
        "Enter space ID (e.g. spaces/ABC123):"
    ).ask()


def _filter_spaces_by_type(spaces):
    """Prompt for space type filter and return matching spaces."""
    selected_types = questionary.checkbox(
        "Select space types to include:",
        choices=SPACE_TYPES,
    ).ask()
    if not selected_types:
        log_info("[yellow]No space types selected.[/yellow]")
        return []
    return [
        s for s in spaces
        if s.get("spaceType") in selected_types
    ]


def _pick_card_payload(space_id=None):
    """Prompt user to choose a card source and return the payload.

    Returns card payload dict, or None if cancelled.
    """
    sources = ["System Alert (built-in)"]
    custom_cards = list_google_cards()
    sources.extend(custom_cards)

    choice = questionary.select(
        "Select card source:", choices=sources
    ).ask()
    if not choice:
        return None

    if choice == "System Alert (built-in)":
        alert_text = questionary.text("Alert text:").ask()
        if not alert_text:
            return None
        sid = space_id or "N/A"
        return build_system_alert_card(sid, alert_text)

    card_data = load_google_card(choice)
    if not card_data:
        log_info(f"[red]Failed to load card: {choice}[/red]")
        return None
    return card_data


def run_gchat_menu(entry):
    """Run the Google Chat interactive action menu."""
    service = create_service(entry["service_account_path"])
    if not service:
        return

    bot_name = entry["name"]

    while True:
        action = questionary.select(
            "Select Google Chat action:",
            choices=[
                "List spaces",
                "Recon space",
                "Send text message (targeted)",
                "Send text message (blast)",
                "Send card message (targeted)",
                "Send card message (blast)",
                "Back to main menu",
            ],
        ).ask()
        if not action or action == "Back to main menu":
            return

        if action == "List spaces":
            list_spaces(service)

        elif action == "Recon space":
            space_id = _pick_space_id()
            if space_id:
                recon_space(service, space_id)

        elif action == "Send text message (targeted)":
            space_id = _pick_space_id()
            if not space_id:
                continue
            message = questionary.text("Message text:").ask()
            if not message:
                continue
            if not confirm_send(
                "Google Chat", "send_text", bot_name,
                [space_id], message,
            ):
                continue
            ok, detail = send_text_message(
                service, space_id, message
            )
            log_result(
                "gchat", "send_text", bot_name, space_id,
                "success" if ok else "failure", detail,
            )

        elif action == "Send text message (blast)":
            spaces = list_spaces(service)
            if not spaces:
                continue
            targets = _filter_spaces_by_type(spaces)
            if not targets:
                continue
            message = questionary.text("Message text:").ask()
            if not message:
                continue
            target_ids = [s["name"] for s in targets]
            if not confirm_send(
                "Google Chat", "send_text_blast", bot_name,
                target_ids, message,
            ):
                continue
            for s in targets:
                ok, detail = send_text_message(
                    service, s["name"], message
                )
                log_result(
                    "gchat", "send_text", bot_name,
                    s["name"],
                    "success" if ok else "failure", detail,
                )

        elif action == "Send card message (targeted)":
            space_id = _pick_space_id()
            if not space_id:
                continue
            card_payload = _pick_card_payload(space_id)
            if not card_payload:
                continue
            if not confirm_send(
                "Google Chat", "send_card", bot_name,
                [space_id], "CardV2 message",
            ):
                continue
            ok, detail = send_card_message(
                service, space_id, card_payload
            )
            log_result(
                "gchat", "send_card", bot_name, space_id,
                "success" if ok else "failure", detail,
            )

        elif action == "Send card message (blast)":
            spaces = list_spaces(service)
            if not spaces:
                continue
            targets = _filter_spaces_by_type(spaces)
            if not targets:
                continue
            card_payload = _pick_card_payload()
            if not card_payload:
                continue
            target_ids = [s["name"] for s in targets]
            if not confirm_send(
                "Google Chat", "send_card_blast", bot_name,
                target_ids, "CardV2 message",
            ):
                continue
            for s in targets:
                ok, detail = send_card_message(
                    service, s["name"], card_payload
                )
                log_result(
                    "gchat", "send_card", bot_name,
                    s["name"],
                    "success" if ok else "failure", detail,
                )
```

**Step 2: Commit**

```bash
git add bot_breacher/gchat/__init__.py
git commit -m "feat(gchat): add interactive menu with all 6 actions"
```

---

### Task 6: Integrate into core CLI and config

**Files:**
- Modify: `bot_breacher/core/config.py:9-13` (add to REQUIRED_FIELDS)
- Modify: `bot_breacher/core/cli.py:31-34` (add to platform choices)
- Modify: `bot_breacher/core/cli.py:104-112` (add elif branch)

**Step 1: Add `gchat` to `REQUIRED_FIELDS` in `core/config.py`**

In `bot_breacher/core/config.py`, add to the `REQUIRED_FIELDS` dict:

```python
REQUIRED_FIELDS = {
    "slack": ["name", "token"],
    "lark": ["name", "app_id", "app_secret"],
    "teams": ["name", "client_id", "client_secret"],
    "gchat": ["name", "service_account_path"],
}
```

**Step 2: Add `"Google Chat"` to `pick_platform()` in `core/cli.py`**

Change the choices list in `pick_platform()`:

```python
def pick_platform():
    """Prompt user to select a messaging platform."""
    return questionary.select(
        "Select a platform:",
        choices=["Slack", "Lark", "Teams", "Google Chat", "Exit"],
    ).ask()
```

**Step 3: Add the `elif` branch in `main()` in `core/cli.py`**

After the Teams elif block (line ~112), add:

```python
        elif platform_key == "google chat":
            from bot_breacher.gchat import run_gchat_menu
            run_gchat_menu(entry)
```

Note: `platform_key` is `platform.lower()` which gives `"google chat"` from `"Google Chat"`. The config key is `gchat`, so we also need to map the display name to the config key. Update the `platform_key` assignment:

Replace the line `platform_key = platform.lower()` and the `get_platform_entries` call with:

```python
        platform_key = platform.lower()
        config_key = "gchat" if platform_key == "google chat" else platform_key
        entries = get_platform_entries(config, config_key)
```

And update all subsequent references to use `config_key` for config lookups while keeping `platform_key` for display routing. The `entries` call already uses the correct variable.

**Step 4: Verify the module loads**

Run: `python -c "from bot_breacher.gchat.auth import create_service; print('OK')"`
Expected: `OK`

Run: `python -c "from bot_breacher.gchat.actions import list_spaces, send_text_message, build_system_alert_card; print('OK')"`
Expected: `OK`

**Step 5: Commit**

```bash
git add bot_breacher/core/config.py bot_breacher/core/cli.py
git commit -m "feat(gchat): integrate Google Chat into platform menu and config"
```

---

### Task 7: Update CLAUDE.md architecture docs

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Update the architecture tree and related docs in CLAUDE.md**

Add `gchat/` to the architecture tree alongside the other platforms. Add `google_cards/` to the Configuration section. Add `google-auth`, `google-api-python-client` to Dependencies.

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add Google Chat module to architecture docs"
```
