# Geppetto

<img width="556" height="381" alt="image" src="https://github.com/user-attachments/assets/c0e0476b-343e-4dec-a935-872773beef0d" />

Offensive security framework for authorized red team and phishing simulation exercises targeting enterprise messaging platforms. Supports **Slack**, **Lark/Feishu**, **Microsoft Teams**, and **Google Chat** through an interactive terminal UI.

> **Disclaimer** This tool is intended for use in authorized penetration testing, red team engagements, and phishing simulations only.

## Features

### Slack
- **Spoofed messages** — send messages with a custom bot name and icon (`chat:write.customize`)
- **Direct messages** — send messages as the bot identity (`chat:write`)
- **File attachments** — send files with accompanying messages (`files:write`)
- **Message search** — search workspace messages by keyword (`search:read`)
- **Channel enumeration** — list all accessible channels (`channels:read`)
- Actions are gated by token permissions — only available operations are shown

### Lark / Feishu
- **Interactive cards** — send rich card messages from pretext JSON templates
- **Card editing** — modify previously sent cards by message ID
- **Email-to-chat resolution** — resolve target emails to Lark chat IDs
- Pretext cards are loaded from the `lark_cards/` directory

### Microsoft Teams
- **Direct messages** — send messages to users via Bot Framework
- **User resolution** — resolve emails to Azure AD user IDs via Graph API
- **Permission enumeration** — decode JWT tokens and list application roles
- Uses OAuth2 client credentials flow for both Bot Framework and Graph API

### Google Chat
- **Space discovery** — list all spaces the bot has access to
- **Space recon** — retrieve space metadata and member lists
- **List bot messages** — list messages sent by the bot in a space
- **Text messages (targeted)** — send plaintext to a specific space
- **Text messages (blast)** — send plaintext to all spaces, filtered by type (Space, Group Chat, DM)
- **Card messages (targeted)** — send CardV2 messages to a specific space
- **Card messages (blast)** — send CardV2 messages to all spaces, filtered by type
- **File attachments (targeted/blast)** — upload and send files with optional text (requires domain-wide delegation)
- **Update messages** — modify previously sent bot messages (text or card)
- **Delete messages** — remove bot-sent messages
- **Create space + add members** — create a named space and invite members by email
- **Capability detection** — automatically enumerates bot permissions on auth
- Built-in System Alert card or custom templates from `google_cards/`
- Uses service account credentials via `google-auth`

### General
- Interactive Rich TUI with platform selection menus
- Multi-bot support — configure multiple credentials per platform
- Bulk targeting from `targets.txt` or single email entry
- Send confirmation prompt before every action
- Dual logging — Rich console output + JSON session logs

## Setup

```bash
pip install -r requirements.txt
cp config.yaml.example config.yaml
```

Edit `config.yaml` with your credentials:

```yaml
slack:
  - name: "My Slack Bot"
    token: "xoxb-your-token-here"

lark:
  - name: "My Lark Bot"
    app_id: "cli_your_app_id"
    app_secret: "your_app_secret"

teams:
  - name: "My Teams Bot"
    client_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    client_secret: "your-client-secret"

gchat:
  - name: "My Google Chat Bot"
    service_account_path: "/path/to/service_account.json"
```

Add target emails to `targets.txt` (one per line) for bulk operations.

## Usage

```bash
python3 -m geppetto
```

The interactive menu walks you through platform selection, credential selection, and action execution. All send actions require explicit confirmation before delivery.

## Project Structure

```
geppetto/
├── __main__.py          # Entry point
├── core/
│   ├── cli.py           # Rich + questionary menus
│   ├── config.py        # YAML config loading
│   ├── logger.py        # Console + JSON file logging
│   └── targets.py       # Target email list parsing
├── slack/
│   ├── auth.py          # Token validation, permission gating
│   └── actions.py       # Spoof, message, attach, search, list
├── lark/
│   ├── auth.py          # Tenant access token acquisition
│   └── actions.py       # Send/edit cards, email resolution
├── teams/
│   ├── auth.py          # OAuth2 client creds, JWT decode
│   └── actions.py       # User resolution, conversation, send
└── gchat/
    ├── auth.py          # Service account credential loading
    └── actions.py       # List spaces, recon, send text/card
```

Each platform follows the same pattern: `auth.py` handles authentication, `actions.py` contains operations, `__init__.py` wires the interactive menu.

## Files

| Path | Purpose |
|------|---------|
| `config.yaml` | Platform credentials (gitignored) |
| `targets.txt` | Target email list (gitignored) |
| `lark_cards/` | Lark interactive card JSON templates |
| `google_cards/` | Google Chat CardV2 JSON templates |
| `logs/` | JSON session logs (gitignored, auto-created) |

## Dependencies

`requests`, `slackclient`, `rich`, `questionary`, `pyyaml`, `google-auth`, `google-api-python-client` — pinned in `requirements.txt`.
