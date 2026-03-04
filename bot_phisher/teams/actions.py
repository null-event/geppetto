"""Teams actions: validate, enumerate, send messages."""

import requests

from bot_phisher.core.logger import log_info


SERVICE_URL = "https://smba.trafficmanager.net/teams/"


def resolve_user_id(graph_token, email):
    """Resolve email to Azure AD user ID via Graph API.

    Returns user ID string or None.
    """
    url = f"https://graph.microsoft.com/v1.0/users/{email}"
    headers = {"Authorization": f"Bearer {graph_token}"}
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code == 200:
            return resp.json().get("id")
        log_info(
            f"[red]Graph user lookup failed for {email}: "
            f"{resp.status_code}[/red]"
        )
    except requests.RequestException as e:
        log_info(f"[red]Graph API error: {e}[/red]")
    return None


def create_conversation(bot_token, bot_app_id, user_id, tenant_id):
    """Create a 1:1 conversation with a Teams user.

    Returns conversation_id or None.
    """
    url = f"{SERVICE_URL}v3/conversations"
    headers = {
        "Authorization": f"Bearer {bot_token}",
        "Content-Type": "application/json",
    }
    body = {
        "bot": {"id": bot_app_id},
        "members": [{"id": f"29:{user_id}"}],
        "channelData": {"tenant": {"id": tenant_id}},
        "isGroup": False,
    }
    try:
        resp = requests.post(url, headers=headers, json=body, timeout=30)
        if resp.status_code in (200, 201):
            return resp.json().get("id")
        log_info(
            f"[red]Create conversation failed ({resp.status_code}): "
            f"{resp.text}[/red]"
        )
    except requests.RequestException as e:
        log_info(f"[red]Bot Framework error: {e}[/red]")
    return None


def send_activity(bot_token, conversation_id, message):
    """Send a message activity to a conversation. Returns (ok, detail)."""
    url = (
        f"{SERVICE_URL}v3/conversations/"
        f"{conversation_id}/activities"
    )
    headers = {
        "Authorization": f"Bearer {bot_token}",
        "Content-Type": "application/json",
    }
    body = {"type": "message", "text": message}
    try:
        resp = requests.post(url, headers=headers, json=body, timeout=30)
        if resp.status_code in (200, 201):
            activity_id = resp.json().get("id", "")
            return True, f"Delivered (activity: {activity_id})"
        return False, f"HTTP {resp.status_code}: {resp.text}"
    except requests.RequestException as e:
        return False, str(e)


def send_message_to_user(
    bot_token, graph_token, bot_app_id, tenant_id, email, message
):
    """Full flow: resolve user, create conversation, send message.

    Returns (ok, detail).
    """
    user_id = resolve_user_id(graph_token, email)
    if not user_id:
        return False, f"Could not resolve user: {email}"

    conv_id = create_conversation(
        bot_token, bot_app_id, user_id, tenant_id
    )
    if not conv_id:
        return False, f"Could not create conversation with {email}"

    return send_activity(bot_token, conv_id, message)
