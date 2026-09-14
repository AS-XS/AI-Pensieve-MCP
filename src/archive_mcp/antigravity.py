import sqlite3
from contextlib import closing
from pathlib import Path
from urllib.parse import unquote, urlparse

from .db import initialize
from .importing import ImportChanges, account_id, conversation_id, upsert_message


def varint(data, position):
    value = shift = 0
    while True:
        byte = data[position]
        position += 1
        value |= (byte & 127) << shift
        if byte < 128:
            return value, position
        shift += 7


def fields(data):
    position = 0
    while position < len(data):
        tag, position = varint(data, position)
        number, wire = tag >> 3, tag & 7
        if wire == 0:
            value, position = varint(data, position)
        elif wire == 1:
            value, position = data[position:position + 8], position + 8
        elif wire == 2:
            size, position = varint(data, position)
            value, position = data[position:position + size], position + size
        elif wire == 5:
            value, position = data[position:position + 4], position + 4
        else:
            raise ValueError(f"unsupported protobuf wire type: {wire}")
        yield number, wire, value


def field(data, number, wire=2):
    return next((value for key, kind, value in fields(data) if key == number and kind == wire), None)


def step_time(payload):
    value = field(field(payload, 5), 1)
    return field(value, 1, 0) + (field(value, 2, 0) or 0) / 1_000_000_000


def step_text(step_type, payload):
    mapping = {14: (19, 2, "user"), 15: (20, 1, "assistant")}
    if step_type not in mapping:
        return None
    container, text_field, role = mapping[step_type]
    text = field(field(payload, container), text_field)
    return (role, text.decode()) if text else None


def workspace(connection):
    blob = connection.execute(
        "SELECT data FROM trajectory_metadata_blob WHERE id = 'main'"
    ).fetchone()[0]
    uri = field(field(blob, 1), 1).decode()
    return Path(unquote(urlparse(uri).path))


def import_file(connection, source, account="default"):
    changes = ImportChanges()
    source = Path(source)
    uri = source.resolve().as_uri() + "?mode=ro&immutable=1"
    with closing(sqlite3.connect(uri, uri=True)) as native:
        selected = []
        for index, step_type, payload in native.execute(
            "SELECT idx, step_type, step_payload FROM steps WHERE status = 3 ORDER BY idx"
        ):
            message = step_text(step_type, payload)
            if message:
                selected.append((index, *message, step_time(payload)))
        if selected:
            trajectory_id = native.execute("SELECT cascade_id FROM trajectory_meta").fetchone()[0]
            project = workspace(native)

    initialize(connection)
    if not selected:
        return changes.result({"conversations": 0, "nodes": 0})
    with connection:
        source_account = account_id(connection, "antigravity", account)
        key = conversation_id(
            connection, source_account, trajectory_id, source,
            f"Antigravity session: {project.name}",
            selected[0][3], selected[-1][3], "local_session",
            changes=changes,
        )
        parent = None
        for index, role, text, created_at in selected:
            node_id = f"step:{index}"
            upsert_message(
                connection, key, node_id, None, parent, role, text, created_at,
                changes=changes,
            )
            parent = node_id

    return changes.result({"conversations": 1, "nodes": len(selected)})
