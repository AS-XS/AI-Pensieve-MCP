import json
from pathlib import Path

from .db import initialize
from .importing import ImportChanges, account_id, conversation_id, upsert_message


def message_text(message):
    if not message:
        return ""
    parts = message.get("content", {}).get("parts", [])
    return "\n".join(part for part in parts if isinstance(part, str))


def import_file(connection, source, account="default"):
    changes = ImportChanges()
    source = Path(source)
    conversations = json.loads(source.read_text(encoding="utf-8-sig"))
    initialize(connection)

    with connection:
        source_account = account_id(connection, "chatgpt", account)

        node_count = 0
        for conversation in conversations:
            source_id = conversation.get("id") or conversation["conversation_id"]
            conversation_key = conversation_id(
                connection,
                source_account,
                source_id,
                source,
                conversation.get("title", ""),
                conversation.get("create_time"),
                conversation.get("update_time"),
                changes=changes,
            )

            for node_id, node in conversation.get("mapping", {}).items():
                message = node.get("message")
                upsert_message(
                    connection,
                    conversation_key,
                    node_id,
                    message.get("id") if message else None,
                    node.get("parent"),
                    message.get("author", {}).get("role") if message else None,
                    message_text(message),
                    message.get("create_time") if message else None,
                    changes=changes,
                )
                node_count += 1

    return changes.result({"conversations": len(conversations), "nodes": node_count})
