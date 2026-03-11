"""Google Chat platform menu and action dispatcher."""

import questionary

from bot_breacher.core.cli import confirm_send
from bot_breacher.core.logger import log_info, log_result
from bot_breacher.gchat.actions import (
    build_system_alert_card,
    list_google_cards,
    list_spaces,
    load_google_card,
    recon_space,
    send_card_message,
    send_text_message,
)
from bot_breacher.gchat.auth import create_service

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


def run_gchat_menu(entry):
    """Run the Google Chat interactive action menu."""
    service = create_service(entry["service_account_path"])
    if not service:
        return

    bot_name = entry["name"]

    while True:
        action = questionary.select(
            "Select Google Chat action:",
            choices=[
                "List spaces",
                "Recon space",
                "Send text message (targeted)",
                "Send text message (blast)",
                "Send card message (targeted)",
                "Send card message (blast)",
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
