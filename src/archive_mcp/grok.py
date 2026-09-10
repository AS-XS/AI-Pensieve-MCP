import json
from pathlib import Path

from .db import initialize
from .importing import account_id, conversation_id, upsert_message


def response_time(response):
    return int(response["create_time"]["$date"]["$numberLong"]) / 1000


def import_file(connection, source, account="default"):
    source = Path(source)
    conversations = json.loads(source.read_text(encoding="utf-8")).get("conversations", [])
    initialize(connection)

    with connection:
        source_account = account_id(connection, "grok", account)
        node_count = 0
        for item in conversations:
            conversation = item["conversation"]
            conversation_key = conversation_id(
                connection,
                source_account,
                conversation["id"],
                source,
                conversation.get("title", ""),
                conversation.get("create_time"),
                conversation.get("modify_time"),
            )
            for wrapper in item.get("responses", []):
                response = wrapper["response"]
                node_id = response["_id"]
                role = "user" if response.get("sender") == "human" else "assistant"
                upsert_message(
                    connection,
                    conversation_key,
                    node_id,
                    node_id,
                    response.get("parent_response_id"),
                    role,
                    response.get("message") or "",
                    response_time(response),
                )
                node_count += 1

    return {"conversations": len(conversations), "nodes": node_count}
