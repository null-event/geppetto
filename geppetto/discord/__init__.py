"""Discord platform menu and action dispatcher."""

import questionary

from geppetto.core.cli import confirm_send
from geppetto.core.logger import log_info, log_result
from geppetto.core.targets import load_targets
from geppetto.discord.actions import (
    list_channels,
    list_guilds,
    send_dm,
    send_file,
    send_message,
    send_webhook_message,
)
from geppetto.discord.auth import get_available_actions, validate_token


def _normalize_webhooks(webhooks):
    """Accept webhooks as list[str], list[{name,url}], or a single {name,url}
    mapping (common YAML mistake of forgetting the list dash). Returns list[dict].
    URLs must start with http(s):// to survive.
    """
    if isinstance(webhooks, dict) and "url" in webhooks:
        webhooks = [webhooks]
    if not isinstance(webhooks, list):
        log_info(
            "[red]webhooks must be a list — check your YAML "
            "(missing '- ' before the item?)[/red]"
        )
        return []

    result = []
    for i, w in enumerate(webhooks):
        if isinstance(w, str):
            url = w
            name = f"webhook[{i}]"
        elif isinstance(w, dict) and "url" in w:
            url = w["url"]
            name = w.get("name") or f"webhook[{i}]"
        else:
            continue
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            log_info(f"[red]Skipping webhook {name!r}: invalid URL {url!r}[/red]")
            continue
        result.append({"name": name, "url": url})
    return result


def _split_ids(raw):
    """Split a manual ID entry string on commas/whitespace."""
    if not raw:
        return []
    return [x.strip() for x in raw.replace(",", " ").split() if x.strip()]


def _pick_guild(token):
    """List guilds and let the user select one. Returns guild dict or None."""
    guilds = list_guilds(token)
    if not guilds:
        log_info("[yellow]No guilds visible to this bot.[/yellow]")
        return None
    choices = [
        questionary.Choice(title=f"{g['name']}  ({g['id']})", value=g)
        for g in guilds
    ]
    return questionary.select("Select guild:", choices=choices).ask()


def _pick_channel_ids(token):
    """Resolve one or more channel IDs via browse / manual / file."""
    method = questionary.select(
        "How to specify channel(s)?",
        choices=[
            "Browse: pick from a guild",
            "Enter channel ID(s) manually",
            "Load channel IDs from targets.txt",
        ],
    ).ask()
    if not method:
        return []

    if method == "Browse: pick from a guild":
        guild = _pick_guild(token)
        if not guild:
            return []
        channels = list_channels(token, guild["id"])
        # Discord channel types: 0 text, 5 announcement, 11/12 threads, 15 forum.
        sendable = [
            c for c in channels if c.get("type") in (0, 5, 10, 11, 12, 15)
        ]
        if not sendable:
            log_info("[yellow]No sendable text channels in that guild.[/yellow]")
            return []
        choices = [
            questionary.Choice(
                title=f"#{c.get('name', '?')}  ({c['id']})",
                value=c["id"],
            )
            for c in sendable
        ]
        picked = questionary.checkbox(
            "Select channel(s) (space to toggle, enter to confirm):",
            choices=choices,
        ).ask()
        return picked or []

    if method == "Enter channel ID(s) manually":
        raw = questionary.text(
            "Channel ID(s), comma or space separated "
            "(Developer Mode → right-click channel → Copy Channel ID):"
        ).ask()
        return _split_ids(raw)

    ids = load_targets()
    if not ids:
        log_info("[yellow]No IDs in targets.txt[/yellow]")
    return ids


def _pick_user_ids():
    """Resolve one or more user IDs via manual entry or targets.txt."""
    method = questionary.select(
        "How to specify user(s)?",
        choices=[
            "Enter user ID(s) manually",
            "Load user IDs from targets.txt",
        ],
    ).ask()
    if not method:
        return []

    if method == "Enter user ID(s) manually":
        raw = questionary.text(
            "User ID(s), comma or space separated "
            "(Developer Mode → right-click user → Copy User ID):"
        ).ask()
        return _split_ids(raw)

    ids = load_targets()
    if not ids:
        log_info("[yellow]No IDs in targets.txt[/yellow]")
    return ids


def run_discord_menu(entry):
    """Run the Discord interactive action menu."""
    token = entry.get("token")
    webhooks = _normalize_webhooks(entry.get("webhooks", []))

    if not token and not webhooks:
        log_info(
            "[red]Discord entry needs at least a 'token' or "
            "'webhooks' field.[/red]"
        )
        return

    if token and not validate_token(token):
        # Token was supplied but invalid. If webhooks exist, fall back to
        # webhook-only mode; otherwise bail.
        if not webhooks:
            return
        log_info(
            "[yellow]Bot token invalid — continuing in "
            "webhook-only mode.[/yellow]"
        )
        token = None

    bot_label = entry["name"]

    while True:
        actions = get_available_actions(bool(token), webhooks)
        action = questionary.select(
            "Select Discord action:", choices=actions
        ).ask()
        if not action or action == "Back to main menu":
            return

        if action == "Validate token":
            validate_token(token)

        elif action == "List guilds":
            list_guilds(token)

        elif action == "List channels in guild":
            guild = _pick_guild(token)
            if not guild:
                continue
            list_channels(token, guild["id"])

        elif action == "Send message (to channel)":
            message = questionary.text("Message text:").ask()
            if not message:
                continue
            targets = _pick_channel_ids(token)
            if not targets:
                continue
            if not confirm_send(
                "Discord", "send_message", bot_label, targets, message
            ):
                continue
            for chan_id in targets:
                ok, detail = send_message(token, chan_id, message)
                log_result(
                    "discord", "send_message", bot_label, chan_id,
                    "success" if ok else "failure", detail,
                )

        elif action == "Send DM (to user)":
            message = questionary.text("Message text:").ask()
            if not message:
                continue
            targets = _pick_user_ids()
            if not targets:
                continue
            if not confirm_send(
                "Discord", "send_dm", bot_label, targets, message
            ):
                continue
            for user_id in targets:
                ok, detail = send_dm(token, user_id, message)
                log_result(
                    "discord", "send_dm", bot_label, user_id,
                    "success" if ok else "failure", detail,
                )

        elif action == "Send file attachment (to channel)":
            file_path = questionary.path("Path to file:").ask()
            if not file_path:
                continue
            message = questionary.text(
                "Accompanying message (optional):"
            ).ask() or ""
            targets = _pick_channel_ids(token)
            if not targets:
                continue
            if not confirm_send(
                "Discord", "send_file", bot_label, targets,
                f"File: {file_path}",
            ):
                continue
            for chan_id in targets:
                ok, detail = send_file(token, chan_id, file_path, message)
                log_result(
                    "discord", "send_file", bot_label, chan_id,
                    "success" if ok else "failure", detail,
                )

        elif action == "Send spoofed message (via webhook)":
            if not webhooks:
                log_info("[red]No webhooks configured in entry[/red]")
                continue
            hook_names = [w["name"] for w in webhooks]
            hook_choice = questionary.select(
                "Select webhook:", choices=hook_names
            ).ask()
            if not hook_choice:
                continue
            hook = next(w for w in webhooks if w["name"] == hook_choice)
            spoof_name = questionary.text(
                "Username to impersonate:"
            ).ask()
            avatar_url = questionary.text(
                "Avatar URL (leave empty for none):"
            ).ask()
            message = questionary.text("Message text:").ask()
            if not message:
                continue
            if not confirm_send(
                "Discord", "send_spoofed", spoof_name or bot_label,
                [hook_choice], message,
            ):
                continue
            ok, detail = send_webhook_message(
                hook["url"], message, spoof_name, avatar_url
            )
            log_result(
                "discord", "send_spoofed", spoof_name or bot_label,
                hook_choice, "success" if ok else "failure", detail,
            )
