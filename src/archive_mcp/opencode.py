import json
from pathlib import Path

from .db import initialize
from .importing import ImportChanges, account_id, conversation_id, upsert_message


def seconds(value):
    return value / 1000 if value and value > 10_000_000_000 else value


def text(message):
    return "\n\n".join(
        part.get("text", "").strip()
        for part in message.get("parts", [])
        if part.get("type") == "text" and part.get("text", "").strip()
    )


def import_file(connection, source, account="default"):
    changes = ImportChanges()
    source = Path(source)
    data = json.loads(source.read_text(encoding="utf-8-sig"))
    info = data["info"]
    selected = [
        (message["info"], body)
        for message in data.get("messages", [])
        if message.get("info", {}).get("role") in ("user", "assistant")
        and (body := text(message))
    ]
    times = info.get("time", {})
    initialize(connection)

    with connection:
        source_account = account_id(connection, "opencode", account)
        key = conversation_id(
            connection, source_account, info["id"], source,
            info.get("title", "OpenCode session"),
            seconds(times.get("created")), seconds(times.get("updated")),
            "local_session",
            changes=changes,
        )
        previous = None
        for message, body in selected:
            node_id = message["id"]
            upsert_message(
                connection, key, node_id, node_id,
                message.get("parentID", previous), message["role"], body,
                seconds(message.get("time", {}).get("created")),
                changes=changes,
            )
            previous = node_id

    return changes.result({"conversations": 1, "nodes": len(selected)})
