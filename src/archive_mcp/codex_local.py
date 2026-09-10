import json
from pathlib import Path

from .db import initialize
from .importing import account_id, conversation_id, upsert_message


INJECTED_PREFIXES = (
    "<environment_context>",
    "<app-context>",
    "<recommended_plugins>",
    "<permissions instructions>",
    "<turn_aborted>",
)
REVIEW_TRANSCRIPT_PREFIX = "The following is the Codex agent history"


def message_text(item):
    role = item.get("role")
    metadata = item.get("internal_chat_message_metadata_passthrough") or {}
    kinds = metadata.get("content_item_kinds")
    texts = []

    for index, part in enumerate(item.get("content", [])):
        if part.get("type") not in ("input_text", "output_text"):
            continue
        text = part.get("text", "").strip()
        if role == "user":
            if kinds and (index >= len(kinds) or kinds[index] != "user.text"):
                continue
            if not kinds and text.startswith(INJECTED_PREFIXES):
                continue
        if text:
            texts.append(text)
    return "\n\n".join(texts)


def messages(rows):
    for line_number, row in enumerate(rows, 1):
        item = row.get("payload", {})
        if row.get("type") != "response_item" or item.get("type") != "message":
            continue
        role = item.get("role")
        if role == "assistant" and item.get("phase") != "final_answer":
            continue
        if role not in ("user", "assistant"):
            continue
        text = message_text(item)
        if text:
            yield line_number, row, item, text


def import_file(connection, source, account="default"):
    source = Path(source)
    rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines()]
    metadata = next(row["payload"] for row in rows if row.get("type") == "session_meta")
    selected = list(messages(rows))
    initialize(connection)

    with connection:
        source_account = account_id(connection, "codex", account)
        source_id = metadata["id"]
        if any(
            role == "user" and text.startswith(REVIEW_TRANSCRIPT_PREFIX)
            for _, _, item, text in selected
            for role in (item.get("role"),)
        ):
            # Codex approval-review sessions contain copied transcripts and
            # reviewer traffic, rather than ordinary user dialogue. Exclude
            # the whole derived session once the marker is observed; the raw
            # JSONL source remains untouched and can be re-imported later.
            connection.execute(
                "DELETE FROM conversations WHERE account_id = ? AND source_id = ?",
                (source_account, source_id),
            )
            return {"conversations": 0, "nodes": 0, "excluded_review_sessions": 1}
        created_at = metadata["timestamp"]
        updated_at = selected[-1][1]["timestamp"] if selected else created_at
        title = f"Codex session: {Path(metadata['cwd']).name}"
        key = conversation_id(
            connection, source_account, source_id, source,
            title, created_at, updated_at, "local_session",
        )
        # Rebuild this derived session snapshot so records excluded by the
        # current parser cannot survive an idempotent re-import.
        connection.execute("DELETE FROM messages WHERE conversation_id = ?", (key,))
        parent = None
        for line_number, row, item, text in selected:
            node_id = f"line:{line_number}"
            upsert_message(
                connection, key, node_id, item.get("id"), parent,
                item["role"], text, row["timestamp"],
            )
            parent = node_id

    return {"conversations": 1, "nodes": len(selected)}
