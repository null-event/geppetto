"""Discord bot token validation."""

import requests

from geppetto.core.logger import log_info


API_BASE = "https://discord.com/api/v10"


def _headers(token):
    return {
        "Authorization": f"Bot {token}",
        "User-Agent": "geppetto (https://github.com/null-event/geppetto, 1.0)",
    }


def validate_token(token):
    """Call GET /users/@me; return bot username#discrim or None."""
    try:
        resp = requests.get(
            f"{API_BASE}/users/@me", headers=_headers(token), timeout=30,
        )
    except requests.RequestException as e:
        log_info(f"[red]Discord connection error: {e}[/red]")
        return None

    if resp.status_code != 200:
        log_info(
            f"[red]Discord auth failed ({resp.status_code}): "
            f"{resp.text}[/red]"
        )
        return None

    data = resp.json()
    username = data.get("username", "unknown")
    discrim = data.get("discriminator", "0")
    bot_id = data.get("id", "?")
    label = f"{username}#{discrim}" if discrim != "0" else username
    log_info(
        f"[green]Authenticated as:[/green] {label} (id={bot_id})"
    )
    return label


def get_available_actions(has_token, webhooks):
    """Return the list of menu actions. Bot/webhook entries gated by auth."""
    actions = []
    if has_token:
        actions.extend([
            "List guilds",
            "List channels in guild",
            "Send message (to channel)",
            "Send DM (to user)",
            "Send file attachment (to channel)",
        ])
    if webhooks:
        actions.append("Send spoofed message (via webhook)")
    if has_token:
        actions.append("Validate token")
    actions.append("Back to main menu")
    return actions
