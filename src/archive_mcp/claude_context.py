import json
from pathlib import Path

from .db import initialize
from .importing import ImportChanges, account_id, upsert_memory


def memory_items(data):
    memory = data[0]
    yield "conversation-memory", "conversation_memory", "Claude conversation memory", memory["conversations_memory"], None
    for project_id, text in memory["project_memories"].items():
        yield f"project-memory:{project_id}", "project_memory", "Claude project memory", text, None


def project_items(project):
    text = "\n".join(filter(None, (project["description"], project["prompt_template"])))
    yield f"project:{project['uuid']}", "project", project["name"], text, project["created_at"]
    for document in project["docs"]:
        yield (
            f"project-document:{project['uuid']}:{document['uuid']}",
            "project_document",
            document["filename"],
            document["content"],
            document["created_at"],
        )


def import_file(connection, source, account="default"):
    changes = ImportChanges()
    source = Path(source)
    data = json.loads(source.read_text(encoding="utf-8-sig"))
    items = list(memory_items(data) if isinstance(data, list) else project_items(data))
    initialize(connection)

    with connection:
        source_account = account_id(connection, "claude", account)
        for source_id, kind, title, text, created_at in items:
            upsert_memory(connection, source_account, source_id, source, kind, title, text, created_at, changes=changes)

    return changes.result({"memories": len(items)})
