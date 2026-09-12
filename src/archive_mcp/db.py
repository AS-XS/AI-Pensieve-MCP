import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path


SCHEMA_VERSION = 1

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS source_accounts (
    id INTEGER PRIMARY KEY,
    provider TEXT NOT NULL,
    label TEXT NOT NULL,
    UNIQUE (provider, label)
);

CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES source_accounts(id),
    source_id TEXT NOT NULL,
    source_file TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT 'conversation',
    title TEXT NOT NULL DEFAULT '',
    created_at REAL,
    updated_at REAL,
    UNIQUE (account_id, source_id)
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    node_source_id TEXT NOT NULL,
    message_source_id TEXT,
    parent_source_id TEXT,
    role TEXT,
    text TEXT NOT NULL DEFAULT '',
    created_at REAL,
    UNIQUE (conversation_id, node_source_id)
);

CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES source_accounts(id),
    source_id TEXT NOT NULL,
    source_file TEXT NOT NULL,
    kind TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL,
    created_at REAL,
    UNIQUE (account_id, source_id)
);

CREATE TABLE IF NOT EXISTS import_batches (
    id INTEGER PRIMARY KEY,
    mode TEXT NOT NULL,
    account TEXT NOT NULL,
    started_at REAL NOT NULL,
    completed_at REAL,
    status TEXT NOT NULL,
    candidate_files INTEGER NOT NULL DEFAULT 0,
    imported_files INTEGER NOT NULL DEFAULT 0,
    warning_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS import_warnings (
    id INTEGER PRIMARY KEY,
    batch_id INTEGER NOT NULL REFERENCES import_batches(id) ON DELETE CASCADE,
    source_format TEXT,
    code TEXT NOT NULL,
    detail TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS import_warnings_batch
ON import_warnings(batch_id);

CREATE VIRTUAL TABLE IF NOT EXISTS message_fts USING fts5(
    text,
    content = messages,
    content_rowid = id
);

CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
    INSERT INTO message_fts(rowid, text) VALUES (new.id, new.text);
END;

CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
    INSERT INTO message_fts(message_fts, rowid, text)
    VALUES ('delete', old.id, old.text);
END;

CREATE TRIGGER IF NOT EXISTS messages_au AFTER UPDATE ON messages BEGIN
    INSERT INTO message_fts(message_fts, rowid, text)
    VALUES ('delete', old.id, old.text);
    INSERT INTO message_fts(rowid, text) VALUES (new.id, new.text);
END;

CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
    text,
    content = memories,
    content_rowid = id
);

CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
    INSERT INTO memory_fts(rowid, text) VALUES (new.id, new.text);
END;

CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
    INSERT INTO memory_fts(memory_fts, rowid, text)
    VALUES ('delete', old.id, old.text);
END;

CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
    INSERT INTO memory_fts(memory_fts, rowid, text)
    VALUES ('delete', old.id, old.text);
    INSERT INTO memory_fts(rowid, text) VALUES (new.id, new.text);
END;
"""


CONVERSATION_FTS_SCHEMA = """
-- Keep the searchable column named text, as in the existing body indexes.
CREATE VIEW conversation_search_content AS
SELECT id, title AS text FROM conversations;

CREATE VIRTUAL TABLE conversation_fts USING fts5(
    text,
    content = conversation_search_content,
    content_rowid = id
);

CREATE TRIGGER conversations_ai AFTER INSERT ON conversations BEGIN
    INSERT INTO conversation_fts(rowid, text) VALUES (new.id, new.title);
END;

CREATE TRIGGER conversations_ad AFTER DELETE ON conversations BEGIN
    INSERT INTO conversation_fts(conversation_fts, rowid, text)
    VALUES ('delete', old.id, old.title);
END;

CREATE TRIGGER conversations_au AFTER UPDATE OF title ON conversations
WHEN old.title IS NOT new.title BEGIN
    INSERT INTO conversation_fts(conversation_fts, rowid, text)
    VALUES ('delete', old.id, old.title);
    INSERT INTO conversation_fts(rowid, text) VALUES (new.id, new.title);
END;

INSERT INTO conversation_fts(conversation_fts) VALUES ('rebuild');
"""


def connect(path, read_only=False):
    if read_only:
        path = f"{Path(path).resolve().as_uri()}?mode=ro"
    connection = sqlite3.connect(path, uri=read_only)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize(connection):
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    if version == SCHEMA_VERSION:
        return
    if version > SCHEMA_VERSION:
        raise ValueError("archive schema is newer than this application")

    # Version 0 covers empty databases and the existing unversioned layouts.
    # Build one transaction so a failed upgrade cannot leave partial DDL/data.
    migration = SCHEMA
    columns = {row[1] for row in connection.execute("PRAGMA table_info(conversations)")}
    if columns and "kind" not in columns:
        migration += """
            ALTER TABLE conversations ADD COLUMN kind TEXT NOT NULL DEFAULT 'conversation';
            UPDATE conversations SET kind = CASE
                WHEN account_id IN (
                    SELECT id FROM source_accounts
                    WHERE provider IN ('codex', 'claude-code', 'antigravity', 'qwen-code')
                ) THEN 'local_session'
                WHEN account_id IN (
                    SELECT id FROM source_accounts WHERE provider = 'gemini'
                ) THEN 'activity_session'
                ELSE 'conversation'
            END;
        """

    if not connection.execute(
        "SELECT 1 FROM sqlite_master WHERE name = 'conversation_fts'"
    ).fetchone():
        migration += CONVERSATION_FTS_SCHEMA

    try:
        connection.executescript(
            "BEGIN;\n" + migration + f"\nPRAGMA user_version = {SCHEMA_VERSION};\nCOMMIT;"
        )
    except Exception:
        connection.rollback()
        raise


def integrity_status(connection):
    database = [row[0] for row in connection.execute("PRAGMA quick_check")]
    foreign_keys = list(connection.execute("PRAGMA foreign_key_check"))
    orphaned = connection.execute(
        """
        SELECT count(*)
        FROM messages child
        JOIN conversations c ON c.id = child.conversation_id
        JOIN source_accounts a ON a.id = c.account_id
        WHERE a.provider != 'claude'
          AND child.parent_source_id IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM messages parent
              WHERE parent.conversation_id = child.conversation_id
                AND parent.node_source_id = child.parent_source_id
          )
        """
    ).fetchone()[0]
    connection.execute("BEGIN")
    try:
        for table in ("message_fts", "memory_fts", "conversation_fts"):
            connection.execute(
                f"INSERT INTO {table}({table}, rank) VALUES ('integrity-check', 1)"
            )
    finally:
        connection.rollback()
    return {
        "ok": database == ["ok"] and not foreign_keys and orphaned == 0,
        "database": "ok" if database == ["ok"] else database,
        "foreign_key_violations": len(foreign_keys),
        "unexpected_orphaned_parents": orphaned,
        "message_fts": "ok",
        "memory_fts": "ok",
        "conversation_fts": "ok",
        "totals": archive_status(connection)["totals"],
    }


def filters(providers, accounts, date_from, date_to, date_column):
    clauses = []
    values = []
    for column, choices in (("a.provider", providers), ("a.label", accounts)):
        if choices:
            clauses.append(f"{column} IN ({','.join('?' for _ in choices)})")
            values.extend(choices)
    if date_from is not None:
        clauses.append(f"{date_column} >= ?")
        values.append(date_from)
    if date_to is not None:
        clauses.append(f"{date_column} <= ?")
        values.append(date_to)
    return "".join(f" AND {clause}" for clause in clauses), values


def _search(
    connection, query, limit, providers, accounts, date_from, date_to,
    conversation_id=None, offset=0,
):
    message_filters, message_values = filters(
        providers, accounts, date_from, date_to, "m.created_at"
    )
    memory_filters, memory_values = filters(
        providers, accounts, date_from, date_to, "m.created_at"
    )
    title_filters, title_values = filters(
        providers, accounts, date_from, date_to, "c.created_at"
    )
    if conversation_id is not None:
        message_filters += " AND c.source_id = ?"
        message_values.append(conversation_id)
        title_filters += " AND c.source_id = ?"
        title_values.append(conversation_id)
        memory_filters += " AND 0"
    rows = connection.execute(
        f"""
        SELECT record_type, record_id, conversation_id, conversation_kind,
               title, provider, account,
               parent_source_id, role, created_at, snippet, matched_field
        FROM (
            SELECT 'message' AS record_type, m.node_source_id AS record_id,
                   c.source_id AS conversation_id, c.kind AS conversation_kind,
                   c.title, a.provider,
                   a.label AS account, m.parent_source_id, m.role,
                   m.created_at,
                   snippet(message_fts, 0, '[', ']', ' … ', 12) AS snippet,
                   'text' AS matched_field, bm25(message_fts) AS score
            FROM message_fts
            JOIN messages m ON m.id = message_fts.rowid
            JOIN conversations c ON c.id = m.conversation_id
            JOIN source_accounts a ON a.id = c.account_id
            WHERE message_fts MATCH ?{message_filters}

            UNION ALL

            SELECT 'memory', m.source_id, NULL, NULL, m.title, a.provider,
                   a.label, NULL, m.kind,
                   m.created_at,
                   snippet(memory_fts, 0, '[', ']', ' … ', 12),
                   'text', bm25(memory_fts)
            FROM memory_fts
            JOIN memories m ON m.id = memory_fts.rowid
            JOIN source_accounts a ON a.id = m.account_id
            WHERE memory_fts MATCH ?{memory_filters}

            UNION ALL

            SELECT 'conversation', c.source_id, c.source_id, c.kind,
                   c.title, a.provider, a.label, NULL, NULL, c.created_at,
                   snippet(conversation_fts, 0, '[', ']', ' … ', 12),
                   'title', bm25(conversation_fts)
            FROM conversation_fts
            JOIN conversations c ON c.id = conversation_fts.rowid
            JOIN source_accounts a ON a.id = c.account_id
            WHERE conversation_fts MATCH ?{title_filters}
        )
        ORDER BY score, record_type, provider, account, conversation_id, record_id
        LIMIT ? OFFSET ?
        """,
        (
            query, *message_values, query, *memory_values,
            query, *title_values, limit, offset,
        ),
    )
    return [dict(row) for row in rows]


def search(connection, query, limit=10, providers=None, accounts=None, date_from=None, date_to=None):
    return _search(
        connection, query, max(1, min(limit, 50)), providers, accounts, date_from, date_to
    )


def search_conversations(
    connection, query, limit=10, providers=None, accounts=None, date_from=None, date_to=None,
):
    """Group the first 50 ranked candidates, preserving their source identities."""
    candidates = search(connection, query, 50, providers, accounts, date_from, date_to)
    groups = {}
    for result in candidates:
        kind = "memory" if result["record_type"] == "memory" else "conversation"
        source_id = result["record_id"] if kind == "memory" else result["conversation_id"]
        key = (kind, result["provider"], result["account"], source_id)
        if key not in groups:
            groups[key] = {
                "group_type": kind,
                "provider": result["provider"], "account": result["account"],
                "conversation_id": result["conversation_id"],
                "conversation_kind": result["conversation_kind"],
                "memory_id": source_id if kind == "memory" else None,
                "title": result["title"],
                "candidate_matches": 0, "matches": [],
            }
        group = groups[key]
        group["candidate_matches"] += 1
        if len(group["matches"]) < 3:
            group["matches"].append(result)
    limit = max(1, min(limit, 50))
    return {
        "groups": list(groups.values())[:limit],
        "candidates_examined": len(candidates),
        "candidate_limit": 50,
        "candidate_limit_reached": len(candidates) == 50,
        "groups_omitted": max(0, len(groups) - limit),
    }


def cross_reference(
    connection, query, limit=10, providers=None, accounts=None,
    date_from=None, date_to=None, candidate_limit=50,
):
    """Search a separate bounded candidate pool for each selected source."""
    candidate_limit = max(1, min(candidate_limit, 200))
    limit = max(1, min(limit, 50))
    clauses, values = filters(providers, accounts, None, None, "")
    source_count = connection.execute(
        f"SELECT count(*) FROM source_accounts a WHERE 1=1{clauses}", values,
    ).fetchone()[0]
    selected = connection.execute(
        f"SELECT provider, label FROM source_accounts a WHERE 1=1{clauses} "
        "ORDER BY provider, label LIMIT ?", (*values, limit),
    ).fetchall()
    bundles = {}
    rows = []
    for source in selected:
        matches = _search(
            connection, query, candidate_limit, [source["provider"]],
            [source["label"]], date_from, date_to,
        )
        bundles[(source["provider"], source["label"])] = {
            "provider": source["provider"],
            "account": source["label"],
            "status": "matches" if matches else "no_matches",
            "candidate_limit_reached": len(matches) == candidate_limit,
            "evidence_omitted": max(0, len(matches) - 5),
            "matched_records": 0,
            "conversations": {},
            "evidence": [],
        }
        rows.extend(matches)
    for result in rows:
        bundle = bundles[(result["provider"], result["account"])]
        bundle["matched_records"] += 1
        conversation_id = result["conversation_id"]
        if conversation_id is not None:
            conversation = bundle["conversations"].setdefault(conversation_id, {
                "conversation_id": conversation_id,
                "conversation_kind": result["conversation_kind"],
                "title": result["title"],
                "dates": [],
            })
            if result["created_at"] is not None:
                conversation["dates"].append(iso_time(result["created_at"]))
        if len(bundle["evidence"]) < 5:
            bundle["evidence"].append({
                "record_type": result["record_type"],
                "record_id": result["record_id"],
                "conversation_id": conversation_id,
                "title": result["title"],
                "role": result["role"],
                "created_at": iso_time(result["created_at"]),
                "matched_field": result["matched_field"],
                "snippet": result["snippet"],
                "provenance": {
                    "provider": result["provider"],
                    "account": result["account"],
                    "conversation_id": conversation_id,
                    "record_type": result["record_type"],
                    "record_id": result["record_id"],
                },
            })
    ordered = []
    for bundle in bundles.values():
        conversations = list(bundle["conversations"].values())
        for conversation in conversations:
            conversation["dates"] = sorted(set(conversation["dates"]))
        bundle["conversations"] = conversations
        bundle["conversation_count"] = len(conversations)
        ordered.append(bundle)
    return {
        "query": query,
        "bundles": ordered,
        "sources_available": source_count,
        "sources_examined": len(selected),
        "sources_unexamined": source_count - len(selected),
        "candidates_examined": len(rows),
        "candidate_limit": candidate_limit,
        "candidate_limit_scope": "per_source",
        "candidate_limit_reached": any(b["candidate_limit_reached"] for b in ordered),
    }


def get_conversation_matches(
    connection, query, provider, account, source_id, offset=0, limit=10,
    date_from=None, date_to=None,
):
    """Expand one group, including matches beyond the global candidate window."""
    conversation_row(connection, provider, account, source_id)
    limit = max(1, min(limit, 50))
    offset = max(0, offset)
    rows = _search(
        connection, query, limit + 1, [provider], [account], date_from, date_to,
        conversation_id=source_id, offset=offset,
    )
    return {
        "matches": rows[:limit],
        "next_offset": offset + limit if len(rows) > limit else None,
    }


def list_conversations(
    connection, limit=50, cursor=0,
    providers=None, accounts=None, date_from=None, date_to=None,
):
    """Page an unchanged archive; restart after any import, refresh, or rebuild."""
    limit = max(1, min(limit, 50))
    cursor = max(0, cursor)
    clauses, values = filters(providers, accounts, date_from, date_to, "c.created_at")
    rows = connection.execute(
        f"""
        SELECT c.id AS archive_id, c.source_id AS conversation_id,
               c.kind AS conversation_kind,
               c.title, a.provider, a.label AS account,
               c.created_at, c.updated_at,
               count(m.id) AS message_count
        FROM conversations c
        JOIN source_accounts a ON a.id = c.account_id
        LEFT JOIN messages m ON m.conversation_id = c.id
        WHERE c.id > ?{clauses}
        GROUP BY c.id
        ORDER BY c.id
        LIMIT ?
        """,
        (cursor, *values, limit + 1),
    ).fetchall()
    has_more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = rows[-1]["archive_id"] if has_more else None
    result = [dict(row) for row in rows]
    for row in result:
        row.pop("archive_id")
        row["created_at"] = iso_time(row["created_at"])
        row["updated_at"] = iso_time(row["updated_at"])
    return {
        "conversations": result,
        "freshness_policy": "restart_after_import_refresh_or_rebuild",
        "next_cursor": next_cursor,
        "has_more": has_more,
    }


def iso_time(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat() if value is not None else None


def timestamp(value, end=False):
    moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    if end and len(value) == 10:
        moment += timedelta(days=1)
        return moment.timestamp() - 0.001
    return moment.timestamp()


def archive_status(connection):
    rows = connection.execute(
        """
        WITH conversation_counts AS (
            SELECT account_id, count(*) AS count FROM conversations GROUP BY account_id
        ), message_counts AS (
            SELECT c.account_id, count(*) AS count
            FROM messages m JOIN conversations c ON c.id = m.conversation_id
            GROUP BY c.account_id
        ), memory_counts AS (
            SELECT account_id, count(*) AS count FROM memories GROUP BY account_id
        ), activity AS (
            SELECT c.account_id, m.created_at
            FROM messages m JOIN conversations c ON c.id = m.conversation_id
            UNION ALL
            SELECT account_id, created_at FROM memories
        ), date_ranges AS (
            SELECT account_id, min(created_at) AS date_from, max(created_at) AS date_to
            FROM activity WHERE created_at IS NOT NULL GROUP BY account_id
        )
        SELECT a.provider, a.label AS account,
               coalesce(c.count, 0) AS conversations,
               coalesce(m.count, 0) AS messages,
               coalesce(mm.count, 0) AS memories,
               d.date_from, d.date_to
        FROM source_accounts a
        LEFT JOIN conversation_counts c ON c.account_id = a.id
        LEFT JOIN message_counts m ON m.account_id = a.id
        LEFT JOIN memory_counts mm ON mm.account_id = a.id
        LEFT JOIN date_ranges d ON d.account_id = a.id
        ORDER BY a.provider, a.label
        """
    ).fetchall()
    sources = [dict(row) for row in rows]
    kind_rows = connection.execute(
        """
        SELECT a.provider, a.label, c.kind, count(*) AS count
        FROM conversations c JOIN source_accounts a ON a.id = c.account_id
        GROUP BY a.provider, a.label, c.kind
        """
    )
    kinds = {}
    for row in kind_rows:
        key = (row["provider"], row["label"])
        kinds.setdefault(key, {})[row["kind"]] = row["count"]
    for source in sources:
        source["date_from"] = iso_time(source["date_from"])
        source["date_to"] = iso_time(source["date_to"])
        source["conversation_kinds"] = kinds.get(
            (source["provider"], source["account"]), {}
        )
    totals_by_kind = {}
    for counts in kinds.values():
        for kind, count in counts.items():
            totals_by_kind[kind] = totals_by_kind.get(kind, 0) + count
    return {
        "schema_version": connection.execute("PRAGMA user_version").fetchone()[0],
        "totals": {
            "accounts": len(sources),
            "conversations": sum(row["conversations"] for row in sources),
            "conversation_kinds": dict(sorted(totals_by_kind.items())),
            "messages": sum(row["messages"] for row in sources),
            "memories": sum(row["memories"] for row in sources),
        },
        "sources": sources,
    }


def list_sources(connection, provider=None, account=None):
    return [
        source for source in archive_status(connection)["sources"]
        if (provider is None or source["provider"] == provider)
        and (account is None or source["account"] == account)
    ]


def conversation_row(connection, provider, account, source_id):
    row = connection.execute(
        """
        SELECT c.id, c.source_id, c.source_file, c.kind, c.title,
               c.created_at, c.updated_at,
               a.provider, a.label AS account
        FROM conversations c JOIN source_accounts a ON a.id = c.account_id
        WHERE a.provider = ? AND a.label = ? AND c.source_id = ?
        """,
        (provider, account, source_id),
    ).fetchone()
    if row is None:
        raise LookupError("conversation not found")
    return dict(row)


def message_dict(row, max_chars=4000):
    result = dict(row)
    result["truncated"] = len(result["text"]) > max_chars
    if result["truncated"]:
        result["text"] = result["text"][:max_chars] + "…"
    return result


def get_message(
    connection, provider, account, source_id, node_source_id, offset=0, limit=4000
):
    """Read an exact character page from one fully attributed message."""
    offset = max(0, offset)
    limit = max(1, min(limit, 4000))
    row = connection.execute(
        """
        SELECT a.provider, a.label AS account, c.source_id AS conversation_id,
               m.node_source_id, m.message_source_id, m.parent_source_id,
               m.role, m.created_at, m.text
        FROM messages m
        JOIN conversations c ON c.id = m.conversation_id
        JOIN source_accounts a ON a.id = c.account_id
        WHERE a.provider = ? AND a.label = ? AND c.source_id = ?
          AND m.node_source_id = ?
        """,
        (provider, account, source_id, node_source_id),
    ).fetchone()
    if row is None:
        raise LookupError("message not found")
    result = dict(row)
    result["total_chars"] = len(result["text"])
    result["text"] = result["text"][offset:offset + limit]
    end = offset + len(result["text"])
    result["offset"] = offset
    result["next_offset"] = end if end < result["total_chars"] else None
    return result


def get_memory(connection, provider, account, source_id):
    row = connection.execute(
        """
        SELECT m.source_id, m.source_file, m.kind, m.title, m.text, m.created_at,
               a.provider, a.label AS account
        FROM memories m JOIN source_accounts a ON a.id = m.account_id
        WHERE a.provider = ? AND a.label = ? AND m.source_id = ?
        """,
        (provider, account, source_id),
    ).fetchone()
    if row is None:
        raise LookupError("memory not found")
    return message_dict(row)


def get_conversation(connection, provider, account, source_id, offset=0, limit=20, newest_first=False):
    conversation = conversation_row(connection, provider, account, source_id)
    limit = max(1, min(limit, 50))
    offset = max(0, offset)
    rows = connection.execute(
        f"""
        SELECT node_source_id, message_source_id, parent_source_id, role, text, created_at
        FROM messages
        WHERE conversation_id = ? AND text <> ''
        ORDER BY {"created_at DESC, id DESC" if newest_first else "id"} LIMIT ? OFFSET ?
        """,
        (conversation["id"], limit + 1, offset),
    ).fetchall()
    undated = connection.execute(
        "SELECT count(*) FROM messages WHERE conversation_id = ? AND text <> '' AND created_at IS NULL",
        (conversation["id"],),
    ).fetchone()[0] if newest_first else None
    conversation.pop("id")
    return {
        "conversation": conversation,
        "messages": [message_dict(row) for row in rows[:limit]],
        "next_offset": offset + limit if len(rows) > limit else None,
        **({"order": "newest_timestamp_first_undated_last", "undated_messages": undated,
            "recency_note": "Includes all branches and independent roots; later messages do not necessarily supersede earlier ones. "
                            "Undated messages cannot be placed chronologically. Check other conversations for project updates too."}
           if newest_first else {}),
    }


def get_message_context(
    connection, provider, account, source_id, node_source_id, before=2, after=2
):
    conversation = conversation_row(connection, provider, account, source_id)
    columns = "node_source_id, message_source_id, parent_source_id, role, text, created_at"
    target = connection.execute(
        f"SELECT {columns} FROM messages WHERE conversation_id = ? AND node_source_id = ?",
        (conversation["id"], node_source_id),
    ).fetchone()
    if target is None:
        raise LookupError("message not found")

    ancestors = []
    parent = target["parent_source_id"]
    depth = 0
    before = max(0, min(before, 10))
    while parent is not None and len(ancestors) < before:
        depth += 1
        row = connection.execute(
            f"SELECT {columns} FROM messages WHERE conversation_id = ? AND node_source_id = ?",
            (conversation["id"], parent),
        ).fetchone()
        if row is None:
            break
        if row["text"]:
            item = message_dict(row)
            item["depth"] = depth
            ancestors.append(item)
        parent = row["parent_source_id"]

    descendants = []
    frontier = [node_source_id]
    for depth in range(1, max(0, min(after, 10)) + 1):
        placeholders = ",".join("?" for _ in frontier)
        rows = connection.execute(
            f"SELECT {columns} FROM messages WHERE conversation_id = ? "
            f"AND parent_source_id IN ({placeholders}) ORDER BY id LIMIT ?",
            (conversation["id"], *frontier, 50 - len(descendants)),
        ).fetchall()
        if not rows:
            break
        for row in rows:
            if row["text"]:
                item = message_dict(row)
                item["depth"] = depth
                descendants.append(item)
        frontier = [row["node_source_id"] for row in rows]
        if len(descendants) == 50:
            break

    conversation.pop("id")
    return {
        "conversation": conversation,
        "ancestors": list(reversed(ancestors)),
        "message": message_dict(target),
        "descendants": descendants,
    }
