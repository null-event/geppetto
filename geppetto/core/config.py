"""Load and validate platform credentials from config.yaml."""

import sys
from pathlib import Path

import yaml


REQUIRED_FIELDS = {
    "slack": ["name", "token"],
    "lark": ["name", "app_id", "app_secret"],
    "teams": ["name", "client_id", "client_secret"],
    "gchat": ["name", "service_account_path"],
    "discord": ["name"],
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
