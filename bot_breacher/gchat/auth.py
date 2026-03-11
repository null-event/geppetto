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
        Tuple of (service, credentials) or (None, None) on failure.
    """
    if not os.path.exists(service_account_path):
        log_info(
            f"[red]Service account file not found: "
            f"{service_account_path}[/red]"
        )
        return None, None

    try:
        creds = service_account.Credentials.from_service_account_file(
            service_account_path, scopes=SCOPES
        )
        service = build("chat", "v1", credentials=creds)
        log_info("[green]Google Chat service authenticated[/green]")
        return service, creds
    except Exception as e:
        log_info(f"[red]Google Chat auth failed: {e}[/red]")
        return None, None


def check_capabilities(service, creds, has_delegate=False):
    """Probe API to determine bot capabilities.

    Tests actual API access and reports available permissions.

    Args:
        service: Google Chat API service object.
        creds: The credentials object used to build the service.
        has_delegate: Whether delegate_user_email is configured.

    Returns:
        Dict of capability name -> bool.
    """
    caps = {
        "messaging": False,
        "spaces_create": False,
        "memberships": False,
        "attachments": False,
    }

    # Test basic messaging access
    try:
        service.spaces().list().execute()
        caps["messaging"] = True
    except Exception:
        pass

    # Check scopes for space creation and membership management
    granted = set(creds.scopes or [])
    if "https://www.googleapis.com/auth/chat.app.spaces.create" in granted:
        caps["spaces_create"] = True
    if "https://www.googleapis.com/auth/chat.app.memberships" in granted:
        caps["memberships"] = True

    # Attachments require domain-wide delegation
    caps["attachments"] = has_delegate

    # Display capabilities
    log_info("[cyan]Bot capabilities:[/cyan]")
    labels = {
        "messaging": "Send/update/delete messages, list spaces",
        "spaces_create": "Create spaces (admin approval required)",
        "memberships": "Manage space members (admin approval required)",
        "attachments": "File attachments (domain-wide delegation)",
    }
    for cap, enabled in caps.items():
        icon = "[green]✓[/green]" if enabled else "[red]✗[/red]"
        log_info(f"  {icon} {labels[cap]}")

    return caps
