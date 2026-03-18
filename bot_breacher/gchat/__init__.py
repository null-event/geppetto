"""Google Chat platform menu and action dispatcher."""

import os

import questionary

from bot_breacher.core.cli import confirm_send, pick_targets_source
from bot_breacher.core.logger import log_info, log_result
from bot_breacher.core.targets import load_targets
from bot_breacher.gchat.actions import (
    add_members_to_space,
    build_system_alert_card,
    create_space,
    delete_message,
    list_bot_messages,
    list_google_cards,
    list_spaces,
    load_google_card,
    recon_space,
    send_card_message,
    send_text_message,
    update_card_message,
    update_text_message,
    upload_attachment,
)
from bot_breacher.gchat.auth import (
    check_capabilities,
    create_delegated_service,
    create_service,
)

SPACE_TYPES = ["SPACE", "GROUP_CHAT", "DIRECT_MESSAGE"]


def _pick_space_id():
    """Prompt for a space ID."""
    return questionary.text(
        "Enter space ID (e.g. spaces/ABC123):"
    ).ask()


def _filter_spaces_by_type(spaces):
    """Prompt for space type filter and return matching spaces."""
    selected_types = questionary.checkbox(
        "Select space types to include:",
        choices=SPACE_TYPES,
    ).ask()
    if not selected_types:
        log_info("[yellow]No space types selected.[/yellow]")
        return []
    return [
        s for s in spaces
        if s.get("spaceType") in selected_types
    ]


def _pick_card_payload(space_id=None):
    """Prompt user to choose a card source and return the payload.

    Returns card payload dict, or None if cancelled.
    """
    sources = ["System Alert (built-in)"]
    custom_cards = list_google_cards()
    sources.extend(custom_cards)

    choice = questionary.select(
        "Select card source:", choices=sources
    ).ask()
    if not choice:
        return None

    if choice == "System Alert (built-in)":
        alert_text = questionary.text("Alert text:").ask()
        if not alert_text:
            return None
        sid = space_id or "N/A"
        return build_system_alert_card(sid, alert_text)

    card_data = load_google_card(choice)
    if not card_data:
        log_info(f"[red]Failed to load card: {choice}[/red]")
        return None
    return card_data


def _pick_message_name(service):
    """Prompt for a message name, with option to list messages first."""
    method = questionary.select(
        "How to specify message?",
        choices=[
            "Enter message name directly",
            "List bot messages in a space first",
        ],
    ).ask()
    if not method:
        return None

    if method == "List bot messages in a space first":
        space_id = _pick_space_id()
        if not space_id:
            return None
        msgs = list_bot_messages(service, space_id)
        if not msgs:
            return None
        names = [m["name"] for m in msgs]
        return questionary.select(
            "Select message:", choices=names
        ).ask()

    return questionary.text(
        "Enter message name (e.g. spaces/ABC/messages/XYZ):"
    ).ask()


def run_gchat_menu(entry):
    """Run the Google Chat interactive action menu."""
    service, creds = create_service(entry["service_account_path"])
    if not service:
        return

    has_delegate = bool(entry.get("delegate_user_email"))
    check_capabilities(service, creds, has_delegate)

    bot_name = entry["name"]

    while True:
        action = questionary.select(
            "Select Google Chat action:",
            choices=[
                "List spaces",
                "Recon space",
                "List bot messages",
                "Send text message (targeted)",
                "Send text message (blast)",
                "Send card message (targeted)",
                "Send card message (blast)",
                "Send attachment (targeted)",
                "Send attachment (blast)",
                "Update message",
                "Delete message",
                "Create space + add members",
                "Back to main menu",
            ],
        ).ask()
        if not action or action == "Back to main menu":
            return

        if action == "List spaces":
            list_spaces(service)

        elif action == "Recon space":
            space_id = _pick_space_id()
            if space_id:
                recon_space(service, space_id)

        elif action == "List bot messages":
            space_id = _pick_space_id()
            if space_id:
                list_bot_messages(service, space_id)

        elif action == "Send text message (targeted)":
            space_id = _pick_space_id()
            if not space_id:
                continue
            message = questionary.text("Message text:").ask()
            if not message:
                continue
            if not confirm_send(
                "Google Chat", "send_text", bot_name,
                [space_id], message,
            ):
                continue
            ok, detail = send_text_message(
                service, space_id, message
            )
            log_result(
                "gchat", "send_text", bot_name, space_id,
                "success" if ok else "failure", detail,
            )

        elif action == "Send text message (blast)":
            spaces = list_spaces(service)
            if not spaces:
                continue
            targets = _filter_spaces_by_type(spaces)
            if not targets:
                continue
            message = questionary.text("Message text:").ask()
            if not message:
                continue
            target_ids = [s["name"] for s in targets]
            if not confirm_send(
                "Google Chat", "send_text_blast", bot_name,
                target_ids, message,
            ):
                continue
            for s in targets:
                ok, detail = send_text_message(
                    service, s["name"], message
                )
                log_result(
                    "gchat", "send_text", bot_name,
                    s["name"],
                    "success" if ok else "failure", detail,
                )

        elif action == "Send card message (targeted)":
            space_id = _pick_space_id()
            if not space_id:
                continue
            card_payload = _pick_card_payload(space_id)
            if not card_payload:
                continue
            if not confirm_send(
                "Google Chat", "send_card", bot_name,
                [space_id], "CardV2 message",
            ):
                continue
            ok, detail = send_card_message(
                service, space_id, card_payload
            )
            log_result(
                "gchat", "send_card", bot_name, space_id,
                "success" if ok else "failure", detail,
            )

        elif action == "Send card message (blast)":
            spaces = list_spaces(service)
            if not spaces:
                continue
            targets = _filter_spaces_by_type(spaces)
            if not targets:
                continue
            card_payload = _pick_card_payload()
            if not card_payload:
                continue
            target_ids = [s["name"] for s in targets]
            if not confirm_send(
                "Google Chat", "send_card_blast", bot_name,
                target_ids, "CardV2 message",
            ):
                continue
            for s in targets:
                ok, detail = send_card_message(
                    service, s["name"], card_payload
                )
                log_result(
                    "gchat", "send_card", bot_name,
                    s["name"],
                    "success" if ok else "failure", detail,
                )

        elif action == "Send attachment (targeted)":
            delegate_email = entry.get("delegate_user_email")
            if not delegate_email:
                log_info(
                    "[red]delegate_user_email required in "
                    "config for attachments[/red]"
                )
                continue
            delegated = create_delegated_service(
                entry["service_account_path"], delegate_email
            )
            if not delegated:
                continue
            space_id = _pick_space_id()
            if not space_id:
                continue
            file_path = questionary.path(
                "File path to upload:"
            ).ask()
            if not file_path:
                continue
            text = questionary.text(
                "Accompanying message (optional, Enter to skip):"
            ).ask() or None
            preview = (
                os.path.basename(file_path)
                + (f" + '{text}'" if text else "")
            )
            if not confirm_send(
                "Google Chat", "send_attachment", bot_name,
                [space_id], preview,
            ):
                continue
            ok, detail = upload_attachment(
                delegated, space_id, file_path, text
            )
            log_result(
                "gchat", "send_attachment", bot_name,
                space_id,
                "success" if ok else "failure", detail,
            )

        elif action == "Send attachment (blast)":
            delegate_email = entry.get("delegate_user_email")
            if not delegate_email:
                log_info(
                    "[red]delegate_user_email required in "
                    "config for attachments[/red]"
                )
                continue
            delegated = create_delegated_service(
                entry["service_account_path"], delegate_email
            )
            if not delegated:
                continue
            spaces = list_spaces(service)
            if not spaces:
                continue
            targets = _filter_spaces_by_type(spaces)
            if not targets:
                continue
            file_path = questionary.path(
                "File path to upload:"
            ).ask()
            if not file_path:
                continue
            text = questionary.text(
                "Accompanying message (optional, Enter to skip):"
            ).ask() or None
            target_ids = [s["name"] for s in targets]
            preview = (
                os.path.basename(file_path)
                + (f" + '{text}'" if text else "")
            )
            if not confirm_send(
                "Google Chat", "send_attachment_blast",
                bot_name, target_ids, preview,
            ):
                continue
            for s in targets:
                ok, detail = upload_attachment(
                    delegated, s["name"], file_path, text
                )
                log_result(
                    "gchat", "send_attachment", bot_name,
                    s["name"],
                    "success" if ok else "failure", detail,
                )

        elif action == "Update message":
            msg_name = _pick_message_name(service)
            if not msg_name:
                continue
            update_type = questionary.select(
                "Update type:",
                choices=["Update text", "Update card"],
            ).ask()
            if not update_type:
                continue
            if update_type == "Update text":
                new_text = questionary.text(
                    "New message text:"
                ).ask()
                if not new_text:
                    continue
                if not confirm_send(
                    "Google Chat", "update_text", bot_name,
                    [msg_name], new_text,
                ):
                    continue
                ok, detail = update_text_message(
                    service, msg_name, new_text
                )
            else:
                card_payload = _pick_card_payload()
                if not card_payload:
                    continue
                if not confirm_send(
                    "Google Chat", "update_card", bot_name,
                    [msg_name], "CardV2 message",
                ):
                    continue
                ok, detail = update_card_message(
                    service, msg_name, card_payload
                )
            log_result(
                "gchat", "update_message", bot_name,
                msg_name,
                "success" if ok else "failure", detail,
            )

        elif action == "Delete message":
            msg_name = _pick_message_name(service)
            if not msg_name:
                continue
            if not confirm_send(
                "Google Chat", "delete_message", bot_name,
                [msg_name], "DELETE message",
            ):
                continue
            ok, detail = delete_message(service, msg_name)
            log_result(
                "gchat", "delete_message", bot_name,
                msg_name,
                "success" if ok else "failure", detail,
            )

        elif action == "Create space + add members":
            customer_id = entry.get("customer_id")
            if not customer_id:
                customer_id = questionary.text(
                    "Google Workspace customer ID "
                    "(found in Admin Console > Account):"
                ).ask()
            if not customer_id:
                continue
            display_name = questionary.text(
                "Space display name:"
            ).ask()
            if not display_name:
                continue
            space_name, detail = create_space(
                service, display_name, customer_id
            )
            if not space_name:
                log_result(
                    "gchat", "create_space", bot_name,
                    "N/A", "failure", detail,
                )
                continue
            log_result(
                "gchat", "create_space", bot_name,
                space_name, "success", detail,
            )
            source = pick_targets_source()
            if source == "Enter single email":
                raw = questionary.text(
                    "Enter emails (comma-separated):"
                ).ask()
                if not raw:
                    continue
                emails = [
                    e.strip()
                    for e in raw.split(",")
                    if e.strip()
                ]
            else:
                emails = load_targets()
            if not emails:
                continue
            log_info(
                f"[cyan]Adding {len(emails)} member(s) to "
                f"{space_name}...[/cyan]"
            )
            results = add_members_to_space(
                service, space_name, emails
            )
            for email, ok, mem_detail in results:
                log_result(
                    "gchat", "add_member", bot_name,
                    email,
                    "success" if ok else "failure",
                    mem_detail,
                )
