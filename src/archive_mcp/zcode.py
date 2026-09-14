"""Read the observed ZCode 3.11.2 native SQLite store after ZCode is closed."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path

from .db import initialize
from .importing import ImportChanges, account_id, conversation_id, upsert_message


REQUIRED_COLUMNS = {
    "session": {"id", "title", "time_created", "time_updated", "title_source"},
    "message": {"id", "session_id", "data", "sequence", "time_created"},
    "part": {"id", "message_id", "session_id", "data", "sequence", "time_created"},
    "session_input": {"admitted_sequence", "promoted_message_id"},
    "schema_migration": {"app_version", "time_applied"},
}


def recognized(connection):
    # The extra tables distinguish this observed store from OpenCode's schema.
    return all(columns <= {
        row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')
    } for table, columns in REQUIRED_COLUMNS.items())


def visible(message):
    semantics = message.get("semantics", {})
    role = message.get("role")
    return (
        not message.get("synthetic")
        and semantics.get("uiVisibility") == "visible"
        and (
            role == "user" and semantics.get("origin") == "real_user"
            and semantics.get("kind") == "user_prompt"
            or role == "assistant" and semantics.get("kind") == "assistant_response"
        )
    )


def import_file(connection, source, account="default"):
    changes = ImportChanges()
    source = Path(source)
    # immutable avoids creating journal/SHM files in the provider's directory.
    # It requires a closed, checkpointed source, not a live WAL database.
    for suffix in ("-wal", "-journal"):
        sidecar = Path(str(source) + suffix)
        if sidecar.exists() and sidecar.stat().st_size:
            raise ValueError("Close ZCode before importing its SQLite session store")
    with closing(sqlite3.connect(
        source.resolve().as_uri() + "?mode=ro&immutable=1", uri=True,
    )) as native:
        native.row_factory = sqlite3.Row
        if not recognized(native):
            raise ValueError("Unsupported ZCode session database schema")
        sessions = list(native.execute("SELECT * FROM session ORDER BY time_created, id"))
        snapshots = []
        for session in sessions:
            rows = list(native.execute(
                "SELECT * FROM message WHERE session_id = ? ORDER BY sequence, time_created, id",
                (session["id"],),
            ))
            messages = {row["id"]: json.loads(row["data"]) for row in rows}
            bodies = {}
            for part in native.execute(
                "SELECT * FROM part WHERE session_id = ? ORDER BY sequence, time_created, id",
                (session["id"],),
            ):
                data = json.loads(part["data"])
                if (data.get("type") == "text" and not data.get("synthetic")
                        and not data.get("ignored") and data.get("text", "").strip()):
                    bodies.setdefault(part["message_id"], []).append(data["text"].strip())
            selected = [row for row in rows if row["id"] in bodies and visible(messages[row["id"]])]
            if selected:
                snapshots.append((session, messages, bodies, selected))

    initialize(connection)
    counts = {"conversations": 0, "nodes": 0}
    with connection:
        for session, messages, bodies, selected in snapshots:
            account_key = account_id(connection, "zcode", account)
            key = conversation_id(
                connection, account_key, session["id"], source, session["title"],
                session["time_created"] / 1000, session["time_updated"] / 1000,
                "local_session",
                changes=changes,
            )
            retained = {row["id"] for row in selected}
            previous = None
            for row in selected:
                message = messages[row["id"]]
                parent = message.get("parentID", previous)
                seen = {row["id"]}
                while parent is not None:
                    if parent in seen:
                        raise ValueError("Cyclic ZCode message ancestry")
                    seen.add(parent)
                    if parent in retained:
                        break
                    parent = messages.get(parent, {}).get("parentID")
                upsert_message(
                    connection, key, row["id"], row["id"], parent,
                    message["role"], "\n\n".join(bodies[row["id"]]), row["time_created"] / 1000,
                    changes=changes,
                )
                previous = row["id"]
            counts["conversations"] += 1
            counts["nodes"] += len(selected)
    return changes.result(counts)
