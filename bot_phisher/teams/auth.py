"""Teams OAuth2 auth, JWT decode, and Graph token acquisition."""

import base64
import json

import requests

from bot_phisher.core.logger import log_info


TOKEN_URL = (
    "https://login.microsoftonline.com/"
    "botframework.com/oauth2/v2.0/token"
)

BOT_SCOPE = "https://api.botframework.com/.default"
GRAPH_SCOPE = "https://graph.microsoft.com/.default"


def _request_token(client_id, client_secret, scope):
    """Request an OAuth2 token. Returns response or None."""
    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": scope,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        return requests.post(
            TOKEN_URL, data=payload, headers=headers, timeout=30,
        )
    except requests.RequestException as e:
        log_info(f"[red]Connection error: {e}[/red]")
        return None


def get_bot_token(client_id, client_secret):
    """Get Bot Framework access token. Returns token string or None."""
    resp = _request_token(client_id, client_secret, BOT_SCOPE)
    if not resp:
        return None
    if resp.status_code == 200:
        token = resp.json().get("access_token")
        log_info("[green]Bot Framework credentials valid[/green]")
        return token
    log_info(
        f"[red]Bot auth failed ({resp.status_code}): "
        f"{resp.text}[/red]"
    )
    return None


def get_graph_token(client_id, client_secret):
    """Get Graph API access token. Returns token string or None."""
    resp = _request_token(client_id, client_secret, GRAPH_SCOPE)
    if not resp:
        return None
    if resp.status_code == 200:
        token = resp.json().get("access_token")
        log_info("[green]Graph API token acquired[/green]")
        return token
    log_info(
        f"[red]Graph auth failed ({resp.status_code}): "
        f"{resp.text}[/red]"
    )
    return None


def decode_jwt_payload(token):
    """Decode JWT payload for inspection. Returns dict or None."""
    try:
        _, payload_b64, _ = token.split(".")
        padding = len(payload_b64) % 4
        if padding:
            payload_b64 += "=" * (4 - padding)
        decoded = base64.b64decode(payload_b64).decode("utf-8")
        return json.loads(decoded)
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as e:
        log_info(f"[red]JWT decode failed: {e}[/red]")
        return None


def enumerate_graph_permissions(token):
    """Decode Graph token and list application permissions."""
    claims = decode_jwt_payload(token)
    if not claims:
        log_info("[red]Failed to decode Graph token[/red]")
        return []
    roles = claims.get("roles", [])
    if roles:
        log_info("[cyan]Application permissions (roles):[/cyan]")
        for role in roles:
            log_info(f"  - {role}")
    else:
        log_info("[yellow]No application roles found in token[/yellow]")
    return roles
