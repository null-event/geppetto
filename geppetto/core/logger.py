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
    _log_file = logs_dir / f"geppetto_{timestamp}.json"


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
