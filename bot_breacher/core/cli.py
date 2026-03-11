"""Interactive CLI menus using Rich and questionary."""

import sys

import questionary
from rich.console import Console
from rich.panel import Panel

from bot_breacher.core.config import get_platform_entries, load_config
from bot_breacher.core.logger import init_log, log_info


console = Console()

BANNER_LINES = [
    ("bold red",    r"  ____        _     ____                      _               "),
    ("bold yellow", r" | __ )  ___ | |_  | __ ) _ __ ___  __ _  ___| |__   ___ _ __ "),
    ("bold green",  r" |  _ \ / _ \| __| |  _ \| '__/ _ \/ _` |/ __| '_ \ / _ \ '__|"),
    ("bold cyan",   r" | |_) | (_) | |_  | |_) | | |  __/ (_| | (__| | | |  __/ |   "),
    ("bold blue",   r" |____/ \___/ \__| |____/|_|  \___|\__,_|\___|_| |_|\___|_|   "),
    ("bold magenta", ""),
    ("bold white",  r"      +-+-+-+-+-+-+-+-+  +-+-+-+-+-+-+-+-+-+-+-+               "),
    ("bold red",    r"      |E|n|t|e|r|p|r|i|s|e|  |M|s|g|  |P|w|n|r|             "),
    ("bold white",  r"      +-+-+-+-+-+-+-+-+--+-+-+-+-+-+-+-+-+-+-+-+               "),
]


def show_banner():
    """Display the bot-breacher banner."""
    console.print()
    for style, line in BANNER_LINES:
        console.print(line, style=style)
    console.print()


def pick_platform():
    """Prompt user to select a messaging platform."""
    return questionary.select(
        "Select a platform:",
        choices=["Slack", "Lark", "Teams", "Google Chat", "Exit"],
    ).ask()


def pick_entry(entries):
    """Prompt user to select a bot/credential entry by name."""
    if len(entries) == 1:
        log_info(f"[cyan]Using:[/cyan] {entries[0]['name']}")
        return entries[0]

    names = [e["name"] for e in entries]
    choice = questionary.select(
        "Select bot/credentials:", choices=names
    ).ask()
    if not choice:
        return None
    return next(e for e in entries if e["name"] == choice)


def pick_targets_source():
    """Prompt user to load targets from file or enter single email."""
    return questionary.select(
        "How to specify targets?",
        choices=[
            "Load from targets.txt",
            "Enter single email",
        ],
    ).ask()


def confirm_send(platform, action, bot_name, targets, message_preview):
    """Show summary and confirm before sending."""
    console.print()
    console.print(
        Panel(
            f"[bold]Platform:[/bold] {platform}\n"
            f"[bold]Action:[/bold] {action}\n"
            f"[bold]Bot:[/bold] {bot_name}\n"
            f"[bold]Targets:[/bold] {len(targets)} recipient(s)\n"
            f"[bold]Preview:[/bold] {message_preview[:200]}",
            title="Send Confirmation",
            border_style="yellow",
        )
    )
    return questionary.confirm("Send messages?", default=False).ask()


def main():
    """Main entry point — platform selection loop."""
    show_banner()
    init_log()
    config = load_config()

    while True:
        platform = pick_platform()
        if not platform or platform == "Exit":
            log_info("[yellow]Exiting bot-breacher.[/yellow]")
            sys.exit(0)

        platform_key = platform.lower()
        config_key = "gchat" if platform_key == "google chat" else platform_key
        entries = get_platform_entries(config, config_key)
        if not entries:
            log_info(
                f"[red]No {platform} credentials in config.yaml.[/red]"
            )
            continue

        entry = pick_entry(entries)
        if not entry:
            continue

        if platform_key == "slack":
            from bot_breacher.slack import run_slack_menu
            run_slack_menu(entry)
        elif platform_key == "lark":
            from bot_breacher.lark import run_lark_menu
            run_lark_menu(entry)
        elif platform_key == "teams":
            from bot_breacher.teams import run_teams_menu
            run_teams_menu(entry)
        elif platform_key == "google chat":
            from bot_breacher.gchat import run_gchat_menu
            run_gchat_menu(entry)
