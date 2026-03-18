# Google Chat Extended Features Design

## Overview

Add update messages, delete messages, create spaces with member addition, and file attachments to the existing Google Chat module in bot-breacher.

## Auth

No changes needed. The existing `chat.bot` scope covers all new operations (messages CRUD, space creation, membership management, media upload).

## Actions API

### Modified functions

**`send_text_message`** and **`send_card_message`** — change success detail from generic "Delivered to {space_id}" to the actual message resource name (e.g. `spaces/ABC/messages/XYZ`). This is backward-compatible since the detail string is only used for logging.

### New functions in `actions.py`

```python
def list_bot_messages(service, space_id) -> list[dict]:
    """List messages in space, filter to bot-sent only.
    Returns list of dicts with name, text preview, createTime.
    Uses spaces.messages.list, filters client-side by sender type BOT."""

def update_text_message(service, message_name, new_text) -> (bool, str):
    """PATCH message with new text content."""

def update_card_message(service, message_name, card_payload) -> (bool, str):
    """PATCH message with new CardV2 content."""

def delete_message(service, message_name) -> (bool, str):
    """DELETE a bot-sent message."""

def create_space(service, display_name) -> (str | None, str):
    """Create a named space. Returns (space_resource_name, detail) or (None, error)."""

def add_members_to_space(service, space_id, emails) -> list[tuple[str, bool, str]]:
    """Add members by email. Returns list of (email, ok, detail)."""

def upload_attachment(service, space_id, file_path, text=None) -> (bool, str):
    """Upload file via media endpoint with optional accompanying text.
    Warns if file exceeds 200MB. Returns (ok, detail)."""
```

## Menu Structure

Updated action menu (6 new items, 13 total):

1. List spaces
2. Recon space
3. List bot messages *(new)*
4. Send text message (targeted)
5. Send text message (blast)
6. Send card message (targeted)
7. Send card message (blast)
8. Send attachment (targeted) *(new)*
9. Send attachment (blast) *(new)*
10. Update message *(new)*
11. Delete message *(new)*
12. Create space + add members *(new)*
13. Back to main menu

## Action Flows

### List bot messages
- Prompt for space ID
- Call `list_bot_messages()`
- Display: message name, text preview (first 80 chars), timestamp
- Read-only, no confirmation needed

### Send attachment (targeted)
- Prompt for space ID
- Prompt for file path
- Warn if file >200MB, ask to continue
- Prompt for optional accompanying text
- `confirm_send()` → `upload_attachment()` → `log_result()`

### Send attachment (blast)
- `list_spaces()` → space type filter
- Prompt for file path + size warning
- Prompt for optional text
- `confirm_send()` → loop `upload_attachment()` → `log_result()`

### Update message
- Prompt for message name (text input, or offer to list bot messages in a space first)
- Choose update type: "Update text" or "Update card"
- If text: prompt for new text
- If card: `_pick_card_payload()` (reuse existing helper)
- `confirm_send()` → `update_text_message()` or `update_card_message()` → `log_result()`

### Delete message
- Prompt for message name (text input, or offer to list bot messages first)
- `confirm_send()` → `delete_message()` → `log_result()`

### Create space + add members
- Prompt for space display name
- `create_space()` → if success:
  - Prompt for member emails: "Load from targets.txt" or "Enter emails (comma-separated)"
  - `add_members_to_space()` → `log_result()` per member

## Files Changed

- Modify: `bot_breacher/gchat/actions.py` — add 7 new functions, modify 2 existing
- Modify: `bot_breacher/gchat/__init__.py` — add 6 new menu items and their flows
