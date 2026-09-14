import json
from pathlib import Path

from .db import initialize
from .importing import ImportChanges, account_id, conversation_id, upsert_message


COMMAND_PREFIXES = ("<command-message>", "<command-name>", "<local-command-stdout>")


def message_text(row):
    message = row.get("message", {})
    content = message.get("content")
    if row.get("type") == "user":
        if row.get("isMeta") or (row.get("origin") or {}).get("kind") == "task-notification":
            return ""
        text = content.strip() if isinstance(content, str) else "\n\n".join(
            part.get("text", "").strip()
            for part in (content or [])
            if part.get("type") == "text" and part.get("text", "").strip()
        )
        return "" if text.startswith(COMMAND_PREFIXES) else text
    if row.get("type") == "assistant" and message.get("stop_reason") == "end_turn":
        return "\n\n".join(
            part.get("text", "").strip()
            for part in (content or [])
            if part.get("type") == "text" and part.get("text", "").strip()
        )
    return ""


def import_file(connection, source, account="default"):
    changes = ImportChanges()
    source = Path(source)
    selected = []
    seen = set()
    session_id = cwd = None

    with source.open(encoding="utf-8-sig") as lines:
        for line in lines:
            row = json.loads(line)
            session_id = session_id or row.get("sessionId")
            cwd = cwd or row.get("cwd")
            text = message_text(row)
            if text and row["uuid"] not in seen:
                seen.add(row["uuid"])
                selected.append((row, text))

    initialize(connection)
    if not selected:
        return changes.result({"conversations": 0, "nodes": 0})
    with connection:
        source_account = account_id(connection, "claude-code", account)
        key = conversation_id(
            connection, source_account, session_id, source,
            f"Claude Code session: {Path(cwd).name}",
            selected[0][0]["timestamp"], selected[-1][0]["timestamp"],
            "local_session",
            changes=changes,
        )
        parent = None
        for row, text in selected:
            node_id = row["uuid"]
            upsert_message(
                connection, key, node_id, row["message"].get("id"), parent,
                row["type"], text, row["timestamp"],
                changes=changes,
            )
            parent = node_id

    return changes.result({"conversations": 1, "nodes": len(selected)})
