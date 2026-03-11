# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bot-breacher is a unified offensive security framework for authorized red team and phishing simulation exercises targeting enterprise messaging platforms (Slack, Lark/Feishu, Microsoft Teams). It provides an interactive Rich TUI CLI with platform-specific attack capabilities.

## Running

```bash
pip install -r requirements.txt
cp config.yaml.example config.yaml  # fill in credentials
python3 -m bot_breacher              # launch interactive menu
```

## Architecture

```
bot_breacher/
├── __main__.py          # Entry point
├── core/
│   ├── cli.py           # Rich + questionary menus, main loop
│   ├── config.py        # YAML config loading/validation
│   ├── logger.py        # Dual output: Rich console + JSON log file
│   └── targets.py       # Parse targets.txt email list
├── slack/
│   ├── __init__.py      # run_slack_menu() — action dispatcher
│   ├── auth.py          # Token validation, permission gating
│   └── actions.py       # spoof, message, attach, search, list channels
├── lark/
│   ├── __init__.py      # run_lark_menu() — action dispatcher
│   ├── auth.py          # Tenant access token acquisition
│   └── actions.py       # send card, edit card, email→chat_id resolution
├── teams/
│   ├── __init__.py      # run_teams_menu() — action dispatcher
│   ├── auth.py          # OAuth2 client creds, JWT decode, Graph token
│   └── actions.py       # user resolution, conversation creation, send message
└── gchat/
    ├── __init__.py      # run_gchat_menu() — action dispatcher
    ├── auth.py          # Service account credential loading, API client
    └── actions.py       # list spaces, recon, send text/card, card helpers
```

Each platform follows the same pattern: `auth.py` handles authentication, `actions.py` contains operations, `__init__.py` wires the interactive menu.

### Data Flow

1. `__main__.py` → `core/cli.main()` — loads config, shows platform menu
2. User picks platform → `core/cli` selects credentials → calls `run_{platform}_menu(entry)`
3. Platform menu authenticates, presents action choices, prompts for targets/message
4. Actions execute against platform APIs, results logged via `core/logger`

### Configuration

- `config.yaml` — platform credentials (gitignored). Supports multiple bots per platform.
- `targets.txt` — one email per line (gitignored). Used by all platforms.
- `pretexts/` — Lark interactive card JSON files. Static, no templating.
- `google_cards/` — Google Chat CardV2 JSON templates. Separate from Lark pretexts.
- `logs/` — JSON session logs (gitignored). Created automatically.

## Key Patterns

- All send actions require explicit confirmation via `core/cli.confirm_send()`
- Platform menus loop until "Back to main menu" is selected
- `log_result()` writes to both Rich console and JSON log file
- `log_info()` prints to console only (auth status, permission lists)
- Credentials are validated on platform entry before showing available actions
- Slack actions are gated by token permissions (only shows what the token can do)
- No automated tests exist

## Legacy Tools

The original standalone tools remain in the repo for reference:
- `EvilSlackbot/` — original Slack tool (has its own .git)
- `LarkBotAbuser2/` — original Lark tool (has its own .git)
- `teams-bot-validator.py` — original Teams validator script

## Dependencies

`requests`, `slackclient`, `rich`, `questionary`, `pyyaml`, `google-auth`, `google-api-python-client` — pinned in `requirements.txt`.
