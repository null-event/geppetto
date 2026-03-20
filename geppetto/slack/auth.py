"""Slack token validation and permission checking."""

from slack import WebClient
from slack.errors import SlackApiError

from geppetto.core.logger import log_info


def create_client(token):
    """Create an authenticated Slack WebClient."""
    return WebClient(token)


def check_permissions(client):
    """Validate token and return (bot_name, permissions_list)."""
    try:
        check = client.api_call("auth.test")
    except SlackApiError as e:
        log_info(f"[red]Slack auth failed: {e.response['error']}[/red]")
        return None, []

    perms = check.headers.get("x-oauth-scopes", "").split(",")
    bot_name = check.get("user", "unknown")

    log_info(f"[green]Authenticated as:[/green] {bot_name}")
    log_info(f"[cyan]Permissions:[/cyan] {', '.join(perms)}")

    return bot_name, perms


def get_available_actions(perms):
    """Return list of action names available for the given permissions."""
    actions = []
    has_channel_read = "channels:read" in perms
    if "chat:write.customize" in perms:
        actions.append("Send spoofed message (to users)")
        if has_channel_read:
            actions.append("Send spoofed message (to channel)")
    if "chat:write" in perms:
        actions.append("Send message (to users)")
        if has_channel_read:
            actions.append("Send message (to channel)")
    if "files:write" in perms:
        actions.append("Send file attachment (to users)")
        if has_channel_read:
            actions.append("Send file attachment (to channel)")
    if "search:read" in perms:
        actions.append("Search for secrets")
    if has_channel_read:
        actions.append("List channels")
    actions.append("Check token permissions")
    actions.append("Back to main menu")
    return actions
