"""Slack platform menu and action dispatcher."""

import questionary

from geppetto.core.cli import confirm_send, pick_targets_source
from geppetto.core.logger import log_info, log_result
from geppetto.core.targets import load_targets
from geppetto.slack.actions import (
    list_channels,
    lookup_channel,
    lookup_user_by_email,
    search_messages,
    send_file,
    send_message,
    send_spoofed_message,
)
from geppetto.slack.auth import (
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
        uid = lookup_user_by_email(client, email)
        if not uid:
            log_info(f"[red]  User not found: {email}[/red]")
            return []
        return [(email, uid)]
    emails = load_targets()
    targets = []
    for email in emails:
        uid = lookup_user_by_email(client, email)
        if uid:
            targets.append((email, uid))
        else:
            log_info(f"[red]  User not found: {email}[/red]")
    return targets


def _get_channel(client):
    """Prompt for a channel name and resolve to channel ID."""
    name = questionary.text(
        "Enter channel name (without #):"
    ).ask()
    if not name:
        return None, None
    name = name.lstrip("#")
    chan_id = lookup_channel(client, name)
    if not chan_id:
        log_info(f"[red]  Channel not found: #{name}[/red]")
        return None, None
    return name, chan_id


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

        elif action == "Send spoofed message (to users)":
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
                ok, detail = send_spoofed_message(
                    client, uid, spoof_name, message, icon_url
                )
                log_result(
                    "slack", "send_spoofed", spoof_name, email,
                    "success" if ok else "failure", detail,
                )

        elif action == "Send spoofed message (to channel)":
            spoof_name = questionary.text(
                "Bot name to impersonate:"
            ).ask()
            icon_url = questionary.text(
                "Icon URL (leave empty for none):"
            ).ask()
            message = questionary.text("Message text:").ask()
            if not message:
                continue
            chan_name, chan_id = _get_channel(client)
            if not chan_id:
                continue
            if not confirm_send(
                "Slack", "spoofed", spoof_name,
                [f"#{chan_name}"], message,
            ):
                continue
            ok, detail = send_spoofed_message(
                client, chan_id, spoof_name, message, icon_url
            )
            log_result(
                "slack", "send_spoofed", spoof_name,
                f"#{chan_name}", "success" if ok else "failure",
                detail,
            )

        elif action == "Send message (to users)":
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
                ok, detail = send_message(client, uid, message)
                log_result(
                    "slack", "send_message", bot_name, email,
                    "success" if ok else "failure", detail,
                )

        elif action == "Send message (to channel)":
            message = questionary.text("Message text:").ask()
            if not message:
                continue
            chan_name, chan_id = _get_channel(client)
            if not chan_id:
                continue
            if not confirm_send(
                "Slack", "message", bot_name,
                [f"#{chan_name}"], message,
            ):
                continue
            ok, detail = send_message(client, chan_id, message)
            log_result(
                "slack", "send_message", bot_name,
                f"#{chan_name}", "success" if ok else "failure",
                detail,
            )

        elif action == "Send file attachment (to users)":
            file_path = questionary.path("Path to file:").ask()
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
                ok, detail = send_file(
                    client, uid, file_path, message, file_title
                )
                log_result(
                    "slack", "send_file", bot_name, email,
                    "success" if ok else "failure", detail,
                )

        elif action == "Send file attachment (to channel)":
            file_path = questionary.path("Path to file:").ask()
            if not file_path:
                continue
            file_title = questionary.text("File title:").ask()
            message = questionary.text(
                "Accompanying message:"
            ).ask()
            chan_name, chan_id = _get_channel(client)
            if not chan_id:
                continue
            if not confirm_send(
                "Slack", "attachment", bot_name,
                [f"#{chan_name}"], f"File: {file_path}",
            ):
                continue
            ok, detail = send_file(
                client, chan_id, file_path, message, file_title
            )
            log_result(
                "slack", "send_file", bot_name,
                f"#{chan_name}", "success" if ok else "failure",
                detail,
            )
