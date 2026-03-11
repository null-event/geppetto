"""Lark/Feishu actions: send card, edit card, resolve chat ID."""

import json
import os

import requests

from bot_breacher.core.logger import log_info
from bot_breacher.lark.auth import BASE_URL


PRETEXTS_DIR = "lark_cards/"


def list_cards():
    """List available pretext card JSON files. Returns list of filenames."""
    if not os.path.isdir(PRETEXTS_DIR):
        log_info(f"[red]Pretexts directory '{PRETEXTS_DIR}' not found[/red]")
        return []
    return [
        f for f in os.listdir(PRETEXTS_DIR)
        if os.path.isfile(os.path.join(PRETEXTS_DIR, f))
        and f.endswith(".json")
    ]


def load_card(filename):
    """Load a pretext card JSON file. Returns JSON string."""
    with open(os.path.join(PRETEXTS_DIR, filename)) as f:
        return json.dumps(json.load(f))


def get_chat_id(token, email):
    """Resolve email to Lark chat_id. Returns chat_id or None."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8",
    }
    try:
        resp = requests.post(
            BASE_URL + "user/v4/email2id",
            headers=headers,
            json={"email": email},
            timeout=30,
        )
        resp.raise_for_status()
        open_id = resp.json().get("data", {}).get("open_id")
        if not open_id:
            log_info(f"[red]Open ID not found for {email}[/red]")
            return None

        resp = requests.get(
            BASE_URL + "chat/v4/p2p/id",
            params={"open_id": open_id},
            headers=headers,
            timeout=30,
        )
        chat_id = resp.json().get("data", {}).get("chat_id")
        if not chat_id:
            log_info(f"[red]Chat ID not found for {email}[/red]")
        return chat_id

    except requests.RequestException as e:
        log_info(f"[red]Lark ID lookup error for {email}: {e}[/red]")
        return None


def send_card(token, chat_id, card_data):
    """Send an interactive card message. Returns (ok, detail)."""
    url = BASE_URL + "im/v1/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    body = {
        "receive_id": chat_id,
        "msg_type": "interactive",
        "content": card_data,
    }
    try:
        resp = requests.post(
            url,
            params={"receive_id_type": "chat_id"},
            headers=headers,
            data=json.dumps(body),
            timeout=30,
        )
        resp.raise_for_status()
        message_id = resp.json().get("data", {}).get("message_id", "")
        return True, f"Sent (message_id: {message_id})"
    except requests.RequestException as e:
        return False, str(e)


def edit_card(token, message_id, card_data):
    """Edit a previously sent card message. Returns (ok, detail)."""
    url = BASE_URL + f"im/v1/messages/{message_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    body = {"content": card_data}
    try:
        resp = requests.patch(
            url, headers=headers,
            data=json.dumps(body), timeout=30,
        )
        resp.raise_for_status()
        return True, f"Edited message_id: {message_id}"
    except requests.RequestException as e:
        return False, str(e)
