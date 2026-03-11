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
