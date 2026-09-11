import json
from pathlib import Path

from .db import initialize
from .importing import account_id, conversation_id, upsert_message


def import_file(connection, source, account="default"):
    source = Path(source)
    conversations = json.loads(source.read_text(encoding="utf-8-sig"))
    initialize(connection)

    with connection:
        source_account = account_id(connection, "claude", account)
        message_count = 0
        for conversation in conversations:
            conversation_key = conversation_id(
                connection,
                source_account,
                conversation["uuid"],
                source,
                conversation.get("name", ""),
                conversation.get("created_at"),
                conversation.get("updated_at"),
            )
            for message in conversation.get("chat_messages", []):
                message_id = message["uuid"]
                role = "user" if message.get("sender") == "human" else message.get("sender")
                upsert_message(
                    connection,
                    conversation_key,
                    message_id,
                    message_id,
                    message.get("parent_message_uuid"),
                    role,
                    message.get("text", ""),
                    message.get("created_at"),
                )
                message_count += 1

    return {"conversations": len(conversations), "nodes": message_count}
