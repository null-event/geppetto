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
        result = service.spaces().messages().create(
            parent=space_id, body={"text": text}
        ).execute()
        msg_name = result.get("name", "unknown")
        return True, msg_name
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
        result = service.spaces().messages().create(
            parent=space_id, body=card_payload
        ).execute()
        msg_name = result.get("name", "unknown")
        return True, msg_name
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
