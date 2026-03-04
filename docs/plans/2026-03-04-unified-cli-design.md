# Bot-Phisher Unified CLI — Design Document

## Overview

Combine three standalone messaging platform attack tools (EvilSlackbot, LarkBotAbuser2, teams-bot-validator) into a single interactive CLI framework called `bot-phisher`. Supports Slack, Lark/Feishu, and Microsoft Teams with a consistent UX across platforms.

## Decisions

- **Architecture:** Package-per-platform with shared core utilities
- **Python:** 3.12 + pip with requirements.txt
- **Credentials:** Single `config.yaml` with sections per platform, gitignored
- **CLI style:** Rich + questionary for interactive TUI menus
- **Targets:** Unified `targets.txt` (one email per line) used by all platforms
- **Lark pretexts:** Static JSON files in `pretexts/`, no templating
- **Logging:** Dual output — rich terminal + structured JSON log file per session
- **Teams messaging:** New functionality — Bot Framework Connector API for sending messages

## Project Structure

```
bot-phisher/
├── bot_phisher/
│   ├── __init__.py
│   ├── __main__.py          # Entry point: python -m bot_phisher
│   ├── core/
│   │   ├── __init__.py
│   │   ├── cli.py           # Rich + questionary menus
│   │   ├── config.py        # YAML config loading/validation
│   │   ├── logger.py        # Dual output: rich console + JSON log file
│   │   └── targets.py       # Parse targets.txt, return email list
│   ├── slack/
│   │   ├── __init__.py
│   │   ├── auth.py           # Token validation, permission check
│   │   └── actions.py        # send_message, send_spoofed, send_file, search, list_channels
│   ├── lark/
│   │   ├── __init__.py
│   │   ├── auth.py           # Tenant access token acquisition
│   │   └── actions.py        # send_card, edit_card, list_bots, list_cards
│   └── teams/
│       ├── __init__.py
│       ├── auth.py           # OAuth2 client credentials, JWT decode, Graph token
│       └── actions.py        # validate_creds, enumerate_graph, send_message
├── config.yaml              # Platform credentials (gitignored)
├── config.yaml.example      # Template with placeholder values
├── targets.txt              # Email list, one per line (gitignored)
├── pretexts/                # Lark card JSON files
├── logs/                    # Session logs (gitignored)
├── requirements.txt
└── README.md
```

## Config Format

```yaml
slack:
  - name: "Engagement Bot"
    token: "xoxb-..."

lark:
  - name: "IT Support On-Call"
    app_id: "cli_xxx"
    app_secret: "xxx"

teams:
  - name: "Phish Bot"
    client_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    client_secret: "your-secret-here"
```

Loaded by `core/config.py`. Validates required fields per platform. Fails fast with actionable error if missing or malformed.

## Interactive CLI Flow

1. **Main menu** — select platform (Slack / Lark / Teams / Exit)
2. **Pick bot/creds** — arrow-key select from configured entries
3. **Authenticate** — validate creds, display permissions/token info
4. **Pick action** — platform-specific menu (see below)
5. **Pick targets** — load from `targets.txt` or enter single email
6. **Compose message** — platform-specific prompts
7. **Confirm** — summary of payload + targets, require explicit yes
8. **Execute** — send per target, show results in Rich table
9. **Loop** — return to action menu or main menu

### Platform Actions

**Slack:**
- Send spoofed message (custom name/icon)
- Send message (as bot)
- Send file attachment
- Search for secrets (keyword)
- List channels
- Check token permissions

**Lark:**
- Send card message
- Edit previous message (by message ID)

**Teams:**
- Validate credentials
- Enumerate Graph API permissions
- Send message to user

## Teams Message Sending (New)

Auth:
1. OAuth2 client credentials → Bot Framework token (`https://api.botframework.com/.default`)
2. Optionally acquire Graph token (`https://graph.microsoft.com/.default`)

Send flow:
1. Get Graph token (needs `User.Read.All`)
2. Resolve email → Azure AD user ID via `/users/{email}`
3. Create 1:1 conversation via Bot Framework Connector (`POST /v3/conversations`)
4. Send activity to conversation (`POST /v3/conversations/{id}/activities`)

v1: plain text messages only. Adaptive Cards deferred.

## Logging

Terminal: Rich console with colored per-target status (green/red) in a live table.

File: `logs/bot_phisher_YYYY-MM-DD_HHMMSS.json` — array of entries:

```json
[
  {
    "timestamp": "2026-03-04T14:30:00Z",
    "platform": "slack",
    "action": "send_spoofed",
    "bot_name": "SecurityBot",
    "target": "user@company.com",
    "status": "success",
    "detail": "Message delivered to U12345"
  }
]
```

`logs/` directory gitignored, created on first run.

## Dependencies

```
requests
slackclient
rich
questionary
pyyaml
```

Dropped: `colorama` (rich replaces it), `lark-oapi` (raw requests suffices).

## Migration Notes

**From EvilSlackbot:** Token permission checking, all 4 attack types, channel listing, email → user ID resolution. Module-level globals replaced with function parameters.

**From LarkBotAbuser2:** Tenant token auth, email → chat_id resolution, card send/edit. `pretexts/` moves to repo root. Bundled venv (`pwd/`, `bin/`, `lib/`) not migrated.

**From teams-bot-validator:** Credential validation, JWT decoding, Graph permission enumeration. New message-sending logic added on top.
