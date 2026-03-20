"""Google Chat actions: list spaces, recon, send text, send cards."""

import json
import os

from googleapiclient.http import MediaFileUpload

from geppetto.core.logger import log_info

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


def list_bot_messages(service, space_id):
    """List bot-sent messages in a space.

    Returns:
        List of dicts with name, text preview, and createTime.
    """
    try:
        result = (
            service.spaces()
            .messages()
            .list(parent=space_id, pageSize=50)
            .execute()
        )
        messages = result.get("messages", [])
        bot_msgs = []
        for msg in messages:
            sender = msg.get("sender", {})
            if sender.get("type") != "BOT":
                continue
            text = msg.get("text", "")
            if not text and msg.get("cardsV2"):
                text = "[CardV2 message]"
            bot_msgs.append({
                "name": msg["name"],
                "preview": text[:80],
                "createTime": msg.get("createTime", ""),
            })

        if not bot_msgs:
            log_info(
                "[yellow]No bot messages found in space.[/yellow]"
            )
            return []

        log_info(
            f"[cyan]Found {len(bot_msgs)} bot message(s):[/cyan]"
        )
        for m in bot_msgs:
            log_info(
                f"  {m['name']} | {m['preview']} | "
                f"{m['createTime']}"
            )
        return bot_msgs
    except Exception as e:
        log_info(f"[red]Failed to list messages: {e}[/red]")
        return []


def update_text_message(service, message_name, new_text):
    """Update a bot-sent message with new text.

    Returns:
        (ok, detail) tuple.
    """
    try:
        service.spaces().messages().patch(
            name=message_name,
            updateMask="text",
            body={"text": new_text},
        ).execute()
        return True, f"Updated {message_name}"
    except Exception as e:
        return False, str(e)


def update_card_message(service, message_name, card_payload):
    """Update a bot-sent message with new CardV2 content.

    Returns:
        (ok, detail) tuple.
    """
    try:
        service.spaces().messages().patch(
            name=message_name,
            updateMask="cardsV2",
            body=card_payload,
        ).execute()
        return True, f"Card updated {message_name}"
    except Exception as e:
        return False, str(e)


def delete_message(service, message_name):
    """Delete a bot-sent message.

    Returns:
        (ok, detail) tuple.
    """
    try:
        service.spaces().messages().delete(
            name=message_name
        ).execute()
        return True, f"Deleted {message_name}"
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


def create_space(service, display_name, customer_id):
    """Create a named space.

    Args:
        service: Google Chat API service object.
        display_name: Name for the new space.
        customer_id: Google Workspace customer ID (required for app auth).

    Returns:
        (space_resource_name, detail) on success, (None, error) on failure.
    """
    try:
        result = service.spaces().create(
            body={
                "displayName": display_name,
                "spaceType": "SPACE",
                "customer": f"customers/{customer_id}",
            }
        ).execute()
        space_name = result.get("name", "unknown")
        log_info(
            f"[green]Created space:[/green] {space_name} "
            f"({display_name})"
        )
        return space_name, f"Created {space_name}"
    except Exception as e:
        log_info(f"[red]Failed to create space: {e}[/red]")
        return None, str(e)


def add_members_to_space(service, space_id, emails):
    """Add members to a space by email.

    Returns:
        List of (email, ok, detail) tuples.
    """
    results = []
    for email in emails:
        try:
            service.spaces().members().create(
                parent=space_id,
                body={
                    "member": {
                        "name": f"users/{email}",
                        "type": "HUMAN",
                    }
                },
            ).execute()
            log_info(f"  [green]+[/green] {email}")
            results.append((email, True, "Added"))
        except Exception as e:
            log_info(f"  [red]x[/red] {email}: {e}")
            results.append((email, False, str(e)))
    return results


MAX_UPLOAD_SIZE_MB = 200


def upload_attachment(service, space_id, file_path, text=None):
    """Upload a file and send it as a message attachment.

    Requires a delegated service (user auth). Warns if file >200MB.

    Returns:
        (ok, detail) tuple.
    """
    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}"

    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb > MAX_UPLOAD_SIZE_MB:
        log_info(
            f"[yellow]Warning: File is {file_size_mb:.1f}MB "
            f"(limit is {MAX_UPLOAD_SIZE_MB}MB)[/yellow]"
        )

    try:
        media = MediaFileUpload(file_path, resumable=True)
        attachment = (
            service.media()
            .upload(
                parent=space_id,
                media_body=media,
                body={
                    "filename": os.path.basename(file_path),
                },
            )
            .execute()
        )
        attachment_name = attachment.get(
            "attachmentDataRef", {}
        ).get("resourceName", "")

        msg_body = {}
        if text:
            msg_body["text"] = text
        msg_body["attachment"] = [
            {
                "contentName": os.path.basename(file_path),
                "attachmentDataRef": {
                    "resourceName": attachment_name,
                },
            }
        ]

        result = (
            service.spaces()
            .messages()
            .create(parent=space_id, body=msg_body)
            .execute()
        )
        msg_name = result.get("name", "unknown")
        return True, msg_name
    except Exception as e:
        return False, str(e)
