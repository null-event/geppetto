"""Load target email addresses from targets.txt."""

from pathlib import Path


def load_targets(path: str = "targets.txt") -> list[str]:
    """Load target email addresses from a text file.

    Reads targets from file (one email per line). Skips blank lines and
    lines starting with "#" (comments). Strips whitespace from each line.

    Args:
        path: Path to the targets file (default: "targets.txt")

    Returns:
        List of email addresses. Empty list if file does not exist.

    Example:
        >>> targets = load_targets("targets.txt")
        >>> print(targets)
        ["user1@example.com", "user2@example.com"]
    """
    target_path = Path(path)

    # Return empty list if file does not exist
    if not target_path.exists():
        return []

    targets = []
    with open(target_path) as f:
        for line in f:
            # Strip whitespace
            stripped = line.strip()

            # Skip blank lines and comments
            if not stripped or stripped.startswith("#"):
                continue

            targets.append(stripped)

    return targets
