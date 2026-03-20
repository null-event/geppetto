# Google Chat Extended Features Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add update messages, delete messages, create spaces with member addition, file attachments, and list bot messages to the Google Chat module.

**Architecture:** Extend `geppetto/gchat/actions.py` with 7 new functions and modify 2 existing ones. Extend `geppetto/gchat/__init__.py` with 6 new menu items. Add additional OAuth scopes in `auth.py` to support new operations. Media upload requires user auth — use domain-wide delegation with a service account impersonating a user.

**Tech Stack:** `google-api-python-client`, `google-auth`, `googleapiclient.http.MediaFileUpload`

---

### Scope Requirements (discovered during research)

The current `chat.bot` scope covers send/update/delete messages. However:

| Feature | Required Scope | Auth Type |
|---------|---------------|-----------|
| Update message | `chat.bot` | App auth (existing) |
| Delete message | `chat.bot` | App auth (existing) |
| List messages | `chat.bot` | App auth (only returns bot messages) |
| Create space | `chat.app.spaces.create` | App auth (admin approval) |
| Add members | `chat.app.memberships` | App auth (admin approval) |
| Media upload | `chat.messages.create` | User auth (domain-wide delegation) |

The auth module needs to add scopes and support domain-wide delegation for the upload feature. The `config.yaml` entry for gchat needs an optional `delegate_user_email` field for uploads.

---

### Task 1: Modify send functions to return message names

**Files:**
- Modify: `geppetto/gchat/actions.py:75-107`

- [ ] **Step 1: Update `send_text_message` to return message resource name**

In `geppetto/gchat/actions.py`, change `send_text_message`:

```python
def send_text_message(service, space_id, text):
    """Send a plaintext message to a space.

    Returns:
        (ok, detail) tuple. Detail is the message resource name on success.
    """
    try:
        result = service.spaces().messages().create(
            parent=space_id, body={"text": text}
        ).execute()
        msg_name = result.get("name", "unknown")
        return True, msg_name
    except Exception as e:
        return False, str(e)
```

- [ ] **Step 2: Update `send_card_message` to return message resource name**

In `geppetto/gchat/actions.py`, change `send_card_message`:

```python
def send_card_message(service, space_id, card_payload):
    """Send a CardV2 message to a space.

    Args:
        service: Google Chat API service object.
        space_id: Space resource name.
        card_payload: Dict with "cardsV2" key.

    Returns:
        (ok, detail) tuple. Detail is the message resource name on success.
    """
    try:
        result = service.spaces().messages().create(
            parent=space_id, body=card_payload
        ).execute()
        msg_name = result.get("name", "unknown")
        return True, msg_name
    except Exception as e:
        return False, str(e)
```

- [ ] **Step 3: Commit**

```bash
git add geppetto/gchat/actions.py
git commit -m "feat(gchat): return message resource names from send functions"
```

---

### Task 2: Add list bot messages, update, and delete functions

**Files:**
- Modify: `geppetto/gchat/actions.py`

- [ ] **Step 1: Add `list_bot_messages` function**

Append to `geppetto/gchat/actions.py`, after the `send_card_message` function:

```python
def list_bot_messages(service, space_id):
    """List bot-sent messages in a space.

    Returns:
        List of dicts with name, text preview, and createTime.
    """
    try:
        result = (
            service.spaces()
            .messages()
            .list(parent=space_id, pageSize=50)
            .execute()
        )
        messages = result.get("messages", [])
        bot_msgs = []
        for msg in messages:
            sender = msg.get("sender", {})
            if sender.get("type") != "BOT":
                continue
            text = msg.get("text", "")
            if not text and msg.get("cardsV2"):
                text = "[CardV2 message]"
            bot_msgs.append({
                "name": msg["name"],
                "preview": text[:80],
                "createTime": msg.get("createTime", ""),
            })

        if not bot_msgs:
            log_info(
                "[yellow]No bot messages found in space.[/yellow]"
            )
            return []

        log_info(
            f"[cyan]Found {len(bot_msgs)} bot message(s):[/cyan]"
        )
        for m in bot_msgs:
            log_info(
                f"  {m['name']} | {m['preview']} | "
                f"{m['createTime']}"
            )
        return bot_msgs
    except Exception as e:
        log_info(f"[red]Failed to list messages: {e}[/red]")
        return []
```

- [ ] **Step 2: Add `update_text_message` function**

```python
def update_text_message(service, message_name, new_text):
    """Update a bot-sent message with new text.

    Returns:
        (ok, detail) tuple.
    """
    try:
        service.spaces().messages().patch(
            name=message_name,
            updateMask="text",
            body={"text": new_text},
        ).execute()
        return True, f"Updated {message_name}"
    except Exception as e:
        return False, str(e)
```

- [ ] **Step 3: Add `update_card_message` function**

```python
def update_card_message(service, message_name, card_payload):
    """Update a bot-sent message with new CardV2 content.

    Returns:
        (ok, detail) tuple.
    """
    try:
        service.spaces().messages().patch(
            name=message_name,
            updateMask="cardsV2",
            body=card_payload,
        ).execute()
        return True, f"Card updated {message_name}"
    except Exception as e:
        return False, str(e)
```

- [ ] **Step 4: Add `delete_message` function**

```python
def delete_message(service, message_name):
    """Delete a bot-sent message.

    Returns:
        (ok, detail) tuple.
    """
    try:
        service.spaces().messages().delete(
            name=message_name
        ).execute()
        return True, f"Deleted {message_name}"
    except Exception as e:
        return False, str(e)
```

- [ ] **Step 5: Commit**

```bash
git add geppetto/gchat/actions.py
git commit -m "feat(gchat): add list bot messages, update, and delete functions"
```

---

### Task 3: Add create space and add members functions

**Files:**
- Modify: `geppetto/gchat/actions.py`
- Modify: `geppetto/gchat/auth.py`

- [ ] **Step 1: Add `chat.app.spaces.create` and `chat.app.memberships` scopes**

In `geppetto/gchat/auth.py`, change the SCOPES list:

```python
SCOPES = [
    "https://www.googleapis.com/auth/chat.bot",
    "https://www.googleapis.com/auth/chat.app.spaces.create",
    "https://www.googleapis.com/auth/chat.app.memberships",
]
```

- [ ] **Step 2: Add `create_space` function**

Append to `geppetto/gchat/actions.py`:

```python
def create_space(service, display_name):
    """Create a named space.

    Returns:
        (space_resource_name, detail) on success, (None, error) on failure.
    """
    try:
        result = service.spaces().create(
            body={
                "displayName": display_name,
                "spaceType": "SPACE",
            }
        ).execute()
        space_name = result.get("name", "unknown")
        log_info(
            f"[green]Created space:[/green] {space_name} "
            f"({display_name})"
        )
        return space_name, f"Created {space_name}"
    except Exception as e:
        log_info(f"[red]Failed to create space: {e}[/red]")
        return None, str(e)
```

- [ ] **Step 3: Add `add_members_to_space` function**

```python
def add_members_to_space(service, space_id, emails):
    """Add members to a space by email.

    Returns:
        List of (email, ok, detail) tuples.
    """
    results = []
    for email in emails:
        try:
            service.spaces().members().create(
                parent=space_id,
                body={
                    "member": {
                        "name": f"users/{email}",
                        "type": "HUMAN",
                    }
                },
            ).execute()
            log_info(f"  [green]+[/green] {email}")
            results.append((email, True, "Added"))
        except Exception as e:
            log_info(f"  [red]x[/red] {email}: {e}")
            results.append((email, False, str(e)))
    return results
```

- [ ] **Step 4: Commit**

```bash
git add geppetto/gchat/actions.py geppetto/gchat/auth.py
git commit -m "feat(gchat): add create space and add members functions"
```

---

### Task 4: Add file upload function

**Files:**
- Modify: `geppetto/gchat/actions.py`
- Modify: `geppetto/gchat/auth.py`
- Modify: `geppetto/core/config.py`

The media upload endpoint requires user authentication. With a service account, this is achieved via domain-wide delegation — the service account impersonates a user. The config needs an optional `delegate_user_email` field.

- [ ] **Step 1: Add `delegate_user_email` as optional config field**

In `geppetto/core/config.py`, the `gchat` entry in `REQUIRED_FIELDS` stays the same (only `name` and `service_account_path` are required). The `delegate_user_email` field is optional and checked at runtime when uploads are attempted.

No code change needed in `config.py` — optional fields aren't validated.

- [ ] **Step 2: Add `create_delegated_service` function to `auth.py`**

Append to `geppetto/gchat/auth.py`:

```python
UPLOAD_SCOPES = [
    "https://www.googleapis.com/auth/chat.messages.create",
]


def create_delegated_service(service_account_path, delegate_email):
    """Create a Chat API service with domain-wide delegation.

    Impersonates the given user for operations requiring user auth
    (e.g. media uploads).

    Returns:
        Google Chat API service object, or None on failure.
    """
    if not os.path.exists(service_account_path):
        log_info(
            f"[red]Service account file not found: "
            f"{service_account_path}[/red]"
        )
        return None

    try:
        creds = service_account.Credentials.from_service_account_file(
            service_account_path, scopes=UPLOAD_SCOPES
        )
        delegated = creds.with_subject(delegate_email)
        service = build("chat", "v1", credentials=delegated)
        log_info(
            f"[green]Delegated service created as "
            f"{delegate_email}[/green]"
        )
        return service
    except Exception as e:
        log_info(
            f"[red]Delegated auth failed: {e}[/red]"
        )
        return None
```

- [ ] **Step 3: Add `upload_attachment` function to `actions.py`**

Add import at top of `actions.py`:

```python
from googleapiclient.http import MediaFileUpload
```

Then append the function:

```python
MAX_UPLOAD_SIZE_MB = 200


def upload_attachment(service, space_id, file_path, text=None):
    """Upload a file and send it as a message attachment.

    Requires a delegated service (user auth). Warns if file >200MB.

    Returns:
        (ok, detail) tuple.
    """
    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}"

    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb > MAX_UPLOAD_SIZE_MB:
        log_info(
            f"[yellow]Warning: File is {file_size_mb:.1f}MB "
            f"(limit is {MAX_UPLOAD_SIZE_MB}MB)[/yellow]"
        )

    try:
        media = MediaFileUpload(file_path, resumable=True)
        attachment = (
            service.media()
            .upload(
                parent=space_id,
                media_body=media,
                body={
                    "filename": os.path.basename(file_path),
                },
            )
            .execute()
        )
        attachment_name = attachment.get("attachmentDataRef", {}).get(
            "resourceName", ""
        )

        msg_body = {}
        if text:
            msg_body["text"] = text
        msg_body["attachment"] = [
            {
                "contentName": os.path.basename(file_path),
                "attachmentDataRef": {
                    "resourceName": attachment_name,
                },
            }
        ]

        result = (
            service.spaces()
            .messages()
            .create(parent=space_id, body=msg_body)
            .execute()
        )
        msg_name = result.get("name", "unknown")
        return True, msg_name
    except Exception as e:
        return False, str(e)
```

- [ ] **Step 4: Update config.yaml.example with optional delegate_user_email**

In `config.yaml.example`, update the gchat section:

```yaml
gchat:
  - name: "Example Google Chat Bot"
    service_account_path: "/path/to/service_account.json"
    # Optional: required for file attachments (domain-wide delegation)
    # delegate_user_email: "admin@example.com"
```

- [ ] **Step 5: Commit**

```bash
git add geppetto/gchat/actions.py geppetto/gchat/auth.py config.yaml.example
git commit -m "feat(gchat): add file upload with domain-wide delegation support"
```

---

### Task 5: Wire new actions into the menu

**Files:**
- Modify: `geppetto/gchat/__init__.py`

- [ ] **Step 1: Add new imports**

In `geppetto/gchat/__init__.py`, update the imports from `actions`:

```python
from geppetto.gchat.actions import (
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
from geppetto.gchat.auth import create_delegated_service, create_service
```

Also add imports for targets:

```python
from geppetto.core.cli import (
    confirm_send,
    pick_targets_source,
)
from geppetto.core.targets import load_targets
```

- [ ] **Step 2: Add `_pick_message_name` helper**

Add after `_pick_space_id`:

```python
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
```

- [ ] **Step 3: Update the action menu choices**

In `run_gchat_menu`, replace the choices list:

```python
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
```

- [ ] **Step 4: Add "List bot messages" handler**

After the "Recon space" elif block, add:

```python
        elif action == "List bot messages":
            space_id = _pick_space_id()
            if space_id:
                list_bot_messages(service, space_id)
```

- [ ] **Step 5: Add "Send attachment (targeted)" handler**

After the "Send card message (blast)" elif block, add:

```python
        elif action == "Send attachment (targeted)":
            delegate_email = entry.get("delegate_user_email")
            if not delegate_email:
                log_info(
                    "[red]delegate_user_email required in config "
                    "for attachments[/red]"
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
            if not confirm_send(
                "Google Chat", "send_attachment", bot_name,
                [space_id],
                f"{os.path.basename(file_path)}"
                + (f" + '{text}'" if text else ""),
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
```

- [ ] **Step 6: Add "Send attachment (blast)" handler**

```python
        elif action == "Send attachment (blast)":
            delegate_email = entry.get("delegate_user_email")
            if not delegate_email:
                log_info(
                    "[red]delegate_user_email required in config "
                    "for attachments[/red]"
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
                f"{os.path.basename(file_path)}"
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
```

- [ ] **Step 7: Add "Update message" handler**

```python
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
```

- [ ] **Step 8: Add "Delete message" handler**

```python
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
```

- [ ] **Step 9: Add "Create space + add members" handler**

```python
        elif action == "Create space + add members":
            display_name = questionary.text(
                "Space display name:"
            ).ask()
            if not display_name:
                continue
            space_name, detail = create_space(
                service, display_name
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
                    e.strip() for e in raw.split(",") if e.strip()
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
```

- [ ] **Step 10: Add `os` import at top of file**

Add to the imports at the top of `__init__.py`:

```python
import os
```

- [ ] **Step 11: Commit**

```bash
git add geppetto/gchat/__init__.py
git commit -m "feat(gchat): wire up 6 new menu actions"
```

---

### Task 6: Update docs

**Files:**
- Modify: `README.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update README Google Chat section**

In `README.md`, replace the Google Chat section with:

```markdown
### Google Chat
- **Space discovery** — list all spaces the bot has access to
- **Space recon** — retrieve space metadata and member lists
- **List bot messages** — list messages sent by the bot in a space
- **Text messages (targeted)** — send plaintext to a specific space
- **Text messages (blast)** — send plaintext to all spaces, filtered by type (Space, Group Chat, DM)
- **Card messages (targeted)** — send CardV2 messages to a specific space
- **Card messages (blast)** — send CardV2 messages to all spaces, filtered by type
- **File attachments (targeted/blast)** — upload and send files with optional text (requires domain-wide delegation)
- **Update messages** — modify previously sent bot messages (text or card)
- **Delete messages** — remove bot-sent messages
- **Create space + add members** — create a named space and invite members by email
- Built-in System Alert card or custom templates from `google_cards/`
- Uses service account credentials via `google-auth`
```

- [ ] **Step 2: Update CLAUDE.md gchat actions.py description**

In the architecture tree in `CLAUDE.md`, update the gchat `actions.py` line:

```
    └── actions.py       # list spaces, recon, send text/card, update/delete, attachments, create space
```

- [ ] **Step 3: Commit**

```bash
git add README.md CLAUDE.md
git commit -m "docs: update Google Chat feature list with new actions"
```
