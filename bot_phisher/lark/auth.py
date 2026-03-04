"""Lark/Feishu tenant access token acquisition."""

import json

import requests

from bot_phisher.core.logger import log_info


BASE_URL = "https://open.feishu.cn/open-apis/"


def get_tenant_token(app_id, app_secret):
    """Acquire a tenant access token. Returns token string or None."""
    url = BASE_URL + "auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json"}
    body = {"app_id": app_id, "app_secret": app_secret}

    try:
        resp = requests.post(
            url, data=json.dumps(body).encode(), headers=headers
        )
        if resp.status_code == 200:
            token = resp.json().get("tenant_access_token", "")
            if token:
                log_info(
                    f"[green]Lark tenant token acquired[/green] "
                    f"({token[:20]}...)"
                )
                return token
            msg = resp.json().get("msg", "unknown error")
            log_info(f"[red]Lark token error: {msg}[/red]")
        else:
            log_info(
                f"[red]Lark token HTTP {resp.status_code}[/red]"
            )
    except requests.RequestException as e:
        log_info(f"[red]Lark connection error: {e}[/red]")

    return None
