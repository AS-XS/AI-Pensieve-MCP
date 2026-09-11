import json
from pathlib import Path

from .db import initialize
from .importing import account_id, upsert_memory


def import_file(connection, source, account="default"):
    source = Path(source)
    document = json.loads(source.read_text(encoding="utf-8-sig"))
    initialize(connection)

    with connection:
        source_account = account_id(connection, document["provider"], account)
        for memory in document["memories"]:
            upsert_memory(
                connection,
                source_account,
                memory["id"],
                source,
                memory["kind"],
                memory.get("title", ""),
                memory["text"],
                memory.get("created_at"),
            )

    return {"memories": len(document["memories"])}
