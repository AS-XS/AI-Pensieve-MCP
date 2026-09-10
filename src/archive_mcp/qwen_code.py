import json
from pathlib import Path

from .db import initialize
from .importing import account_id, conversation_id, upsert_message


def message_text(row):
    message = row.get("message", {})
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    return "\n\n".join(
        part.get("text", "").strip()
        for part in message.get("parts", [])
        if not part.get("thought") and part.get("text", "").strip()
    )


def load(source):
    if source.suffix.lower() == ".json":
        data = json.loads(source.read_text(encoding="utf-8-sig"))
        return {**data.get("metadata", {}), **data}, data.get("messages", [])

    rows = [
        json.loads(line) for line in source.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]
    if rows and rows[0].get("type") == "session_metadata":
        return rows[0], rows[1:]
    first = next(row for row in rows if row.get("sessionId"))
    return {
        "sessionId": first["sessionId"],
        "startTime": first.get("timestamp"),
        "cwd": first.get("cwd"),
    }, rows


def import_file(connection, source, account="default"):
    source = Path(source)
    metadata, rows = load(source)
    selected = [
        (row, body) for row in rows
        if row.get("type") in ("user", "assistant")
        and (body := message_text(row))
    ]
    parents = {
        row["uuid"]: row.get("parentUuid") for row in rows if row.get("uuid")
    }
    visible = {row["uuid"] for row, _ in selected}
    initialize(connection)

    with connection:
        source_account = account_id(connection, "qwen-code", account)
        cwd = metadata.get("cwd")
        title = f"Qwen Code session: {Path(cwd).name}" if cwd else "Qwen Code session"
        key = conversation_id(
            connection, source_account, metadata["sessionId"], source, title,
            metadata.get("startTime"),
            selected[-1][0].get("timestamp") if selected else metadata.get("startTime"),
            "local_session",
        )
        for row, body in selected:
            parent = row.get("parentUuid")
            while parent and parent not in visible:
                parent = parents.get(parent)
            upsert_message(
                connection, key, row["uuid"], row["uuid"], parent,
                row["type"], body, row.get("timestamp"),
            )

    return {"conversations": 1, "nodes": len(selected)}
