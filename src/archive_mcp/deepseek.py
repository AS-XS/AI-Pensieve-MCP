import json
from pathlib import Path

from .db import initialize
from .importing import ImportChanges, account_id, conversation_id, upsert_message


ROLES = {"REQUEST": "user", "RESPONSE": "assistant", "FILE": "user"}


def message_data(message):
    if not message:
        return None, ""
    role = None
    parts = []
    for fragment in message.get("fragments", []):
        kind = fragment.get("type")
        role = role or ROLES.get(kind)
        content = fragment.get("content")
        if kind in {"REQUEST", "RESPONSE"} and isinstance(content, str):
            parts.append(content)
    return role, "\n".join(parts)


def import_file(connection, source, account="default"):
    changes = ImportChanges()
    source = Path(source)
    conversations = json.loads(source.read_text(encoding="utf-8-sig"))
    initialize(connection)

    with connection:
        source_account = account_id(connection, "deepseek", account)
        node_count = 0
        for conversation in conversations:
            conversation_key = conversation_id(
                connection,
                source_account,
                conversation["id"],
                source,
                conversation.get("title", ""),
                conversation.get("inserted_at"),
                conversation.get("updated_at"),
                changes=changes,
            )
            for node_id, node in conversation.get("mapping", {}).items():
                message = node.get("message")
                role, text = message_data(message)
                upsert_message(
                    connection,
                    conversation_key,
                    node_id,
                    node_id if message else None,
                    node.get("parent"),
                    role,
                    text,
                    message.get("inserted_at") if message else None,
                    changes=changes,
                )
                node_count += 1

    return changes.result({"conversations": len(conversations), "nodes": node_count})
