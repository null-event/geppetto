"""Teams platform menu and action dispatcher."""

import questionary

from bot_phisher.core.cli import confirm_send, pick_targets_source
from bot_phisher.core.logger import log_info, log_result
from bot_phisher.core.targets import load_targets
from bot_phisher.teams.actions import send_message_to_user
from bot_phisher.teams.auth import (
    decode_jwt_payload,
    enumerate_graph_permissions,
    get_bot_token,
    get_graph_token,
)


def run_teams_menu(entry):
    """Run the Teams interactive action menu."""
    client_id = entry["client_id"]
    client_secret = entry["client_secret"]

    bot_token = get_bot_token(client_id, client_secret)

    while True:
        action = questionary.select(
            "Select Teams action:",
            choices=[
                "Validate credentials",
                "Enumerate Graph API permissions",
                "Send message to user",
                "Back to main menu",
            ],
        ).ask()
        if not action or action == "Back to main menu":
            return

        if action == "Validate credentials":
            if bot_token:
                log_info("[green]Bot Framework: VALID[/green]")
            else:
                bot_token = get_bot_token(client_id, client_secret)

            graph_token = get_graph_token(client_id, client_secret)
            if graph_token:
                log_info("[green]Graph API: VALID[/green]")

        elif action == "Enumerate Graph API permissions":
            graph_token = get_graph_token(client_id, client_secret)
            if graph_token:
                enumerate_graph_permissions(graph_token)

        elif action == "Send message to user":
            if not bot_token:
                log_info(
                    "[red]Bot token required. "
                    "Run 'Validate credentials' first.[/red]"
                )
                continue

            graph_token = get_graph_token(client_id, client_secret)
            if not graph_token:
                log_info(
                    "[red]Graph token required for user resolution. "
                    "Ensure app has User.Read.All permission.[/red]"
                )
                continue

            # Get tenant ID from bot token
            claims = decode_jwt_payload(bot_token)
            tenant_id = ""
            if claims:
                tenant_id = claims.get(
                    "tid", claims.get("appid", "")
                )

            if not tenant_id:
                tenant_id = questionary.text(
                    "Enter Azure tenant ID:"
                ).ask()
                if not tenant_id:
                    continue

            message = questionary.text("Message text:").ask()
            if not message:
                continue

            source = pick_targets_source()
            if source == "Enter single email":
                email = questionary.text(
                    "Enter target email:"
                ).ask()
                if not email:
                    continue
                emails = [email]
            else:
                emails = load_targets()

            if not confirm_send(
                "Teams", "send_message", entry["name"],
                emails, message,
            ):
                continue

            for email in emails:
                ok, detail = send_message_to_user(
                    bot_token, graph_token, client_id,
                    tenant_id, email, message,
                )
                log_result(
                    "teams", "send_message", entry["name"],
                    email, "success" if ok else "failure", detail,
                )
