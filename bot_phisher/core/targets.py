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
