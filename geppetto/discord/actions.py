"""Discord attack actions: send, DM, attach, list guilds/channels, webhook spoof."""

import os

import requests

from geppetto.core.logger import log_info
from geppetto.discord.auth import API_BASE, _headers


def _post_json(token, path, payload):
    return requests.post(
        f"{API_BASE}{path}", headers={
            **_headers(token), "Content-Type": "application/json",
        }, json=payload, timeout=30,
    )


def _get(token, path):
    return requests.get(
        f"{API_BASE}{path}", headers=_headers(token), timeout=30,
    )


def list_guilds(token):
    """List guilds the bot is a member of. Returns list of guild dicts."""
    try:
        resp = _get(token, "/users/@me/guilds")
    except requests.RequestException as e:
        log_info(f"[red]Guild list error: {e}[/red]")
        return []
    if resp.status_code != 200:
        log_info(
            f"[red]Guild list failed ({resp.status_code}): "
            f"{resp.text}[/red]"
        )
        return []
    guilds = resp.json()
    for g in guilds:
        log_info(f"  {g['id']}  {g['name']}")
    return guilds


def list_channels(token, guild_id):
    """List channels in a guild. Returns list of channel dicts."""
    try:
        resp = _get(token, f"/guilds/{guild_id}/channels")
    except requests.RequestException as e:
        log_info(f"[red]Channel list error: {e}[/red]")
        return []
    if resp.status_code != 200:
        log_info(
            f"[red]Channel list failed ({resp.status_code}): "
            f"{resp.text}[/red]"
        )
        return []
    channels = resp.json()
    for c in channels:
        log_info(f"  {c['id']}  #{c.get('name', '?')}  (type={c.get('type')})")
    return channels


def send_message(token, channel_id, content):
    """Send a message to a channel."""
    try:
        resp = _post_json(
            token, f"/channels/{channel_id}/messages", {"content": content},
        )
    except requests.RequestException as e:
        return False, str(e)
    if resp.status_code in (200, 201):
        msg_id = resp.json().get("id", "?")
        return True, f"Delivered (message id={msg_id})"
    return False, f"HTTP {resp.status_code}: {resp.text}"


def send_dm(token, user_id, content):
    """Open a DM channel with a user and send a message."""
    try:
        resp = _post_json(
            token, "/users/@me/channels", {"recipient_id": str(user_id)},
        )
    except requests.RequestException as e:
        return False, str(e)
    if resp.status_code not in (200, 201):
        return False, (
            f"DM channel open failed ({resp.status_code}): {resp.text}"
        )
    dm_channel_id = resp.json().get("id")
    if not dm_channel_id:
        return False, "DM channel id missing in response"
    return send_message(token, dm_channel_id, content)


def send_file(token, channel_id, file_path, content=""):
    """Upload a file to a channel with optional text content."""
    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}"
    try:
        with open(file_path, "rb") as fh:
            files = {"files[0]": (os.path.basename(file_path), fh)}
            data = {"content": content} if content else {}
            resp = requests.post(
                f"{API_BASE}/channels/{channel_id}/messages",
                headers=_headers(token), files=files, data=data, timeout=60,
            )
    except requests.RequestException as e:
        return False, str(e)
    if resp.status_code in (200, 201):
        return True, f"File sent to {channel_id}"
    return False, f"HTTP {resp.status_code}: {resp.text}"


def send_webhook_message(webhook_url, content, username=None, avatar_url=None):
    """Send a message via webhook with optional custom username/avatar."""
    payload = {"content": content}
    if username:
        payload["username"] = username
    if avatar_url:
        payload["avatar_url"] = avatar_url
    try:
        resp = requests.post(webhook_url, json=payload, timeout=30)
    except requests.RequestException as e:
        return False, str(e)
    if resp.status_code in (200, 204):
        return True, "Webhook delivered"
    return False, f"HTTP {resp.status_code}: {resp.text}"
