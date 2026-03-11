"""Lark platform menu and action dispatcher."""

import questionary

from bot_breacher.core.cli import confirm_send, pick_targets_source
from bot_breacher.core.logger import log_info, log_result
from bot_breacher.core.targets import load_targets
from bot_breacher.lark.actions import (
    edit_card,
    get_chat_id,
    list_cards,
    load_card,
    send_card,
)
from bot_breacher.lark.auth import get_tenant_token


def run_lark_menu(entry):
    """Run the Lark interactive action menu."""
    token = get_tenant_token(entry["app_id"], entry["app_secret"])
    if not token:
        return

    while True:
        action = questionary.select(
            "Select Lark action:",
            choices=[
                "Send card message",
                "Edit previous message",
                "Back to main menu",
            ],
        ).ask()
        if not action or action == "Back to main menu":
            return

        cards = list_cards()
        if not cards:
            log_info("[red]No pretext cards found in lark_cards/[/red]")
            continue

        card_choice = questionary.select(
            "Select pretext card:", choices=cards
        ).ask()
        if not card_choice:
            continue
        card_data = load_card(card_choice)

        if action == "Edit previous message":
            msg_id = questionary.text(
                "Message ID to edit (starts with om_):"
            ).ask()
            if not msg_id:
                continue
            ok, detail = edit_card(token, msg_id, card_data)
            log_result(
                "lark", "edit_card", entry["name"], msg_id,
                "success" if ok else "failure", detail,
            )
            continue

        # Send card message
        source = pick_targets_source()
        if source == "Enter single email":
            email = questionary.text("Enter target email:").ask()
            if not email:
                continue
            emails = [email]
        else:
            emails = load_targets()

        if not confirm_send(
            "Lark", "send_card", entry["name"], emails, card_choice
        ):
            continue

        for email in emails:
            chat_id = get_chat_id(token, email)
            if not chat_id:
                log_result(
                    "lark", "send_card", entry["name"],
                    email, "failure", "Chat ID not resolved",
                )
                continue
            ok, detail = send_card(token, chat_id, card_data)
            log_result(
                "lark", "send_card", entry["name"], email,
                "success" if ok else "failure", detail,
            )
