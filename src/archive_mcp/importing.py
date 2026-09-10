from datetime import datetime


def timestamp(value):
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    return value


def account_id(connection, provider, label):
    connection.execute(
        "INSERT OR IGNORE INTO source_accounts(provider, label) VALUES (?, ?)",
        (provider, label),
    )
    return connection.execute(
        "SELECT id FROM source_accounts WHERE provider = ? AND label = ?",
        (provider, label),
    ).fetchone()[0]


def conversation_id(
    connection, account, source_id, source_file, title, created_at, updated_at,
    kind="conversation",
):
    connection.execute(
        """
        INSERT INTO conversations(
            account_id, source_id, source_file, kind, title, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(account_id, source_id) DO UPDATE SET
            source_file = excluded.source_file,
            kind = excluded.kind,
            title = excluded.title,
            created_at = excluded.created_at,
            updated_at = excluded.updated_at
        """,
        (
            account, source_id, str(source_file), kind, title,
            timestamp(created_at), timestamp(updated_at),
        ),
    )
    return connection.execute(
        "SELECT id FROM conversations WHERE account_id = ? AND source_id = ?",
        (account, source_id),
    ).fetchone()[0]


def upsert_message(connection, conversation, node_id, message_id, parent_id, role, text, created_at):
    connection.execute(
        """
        INSERT INTO messages(
            conversation_id, node_source_id, message_source_id,
            parent_source_id, role, text, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(conversation_id, node_source_id) DO UPDATE SET
            message_source_id = excluded.message_source_id,
            parent_source_id = excluded.parent_source_id,
            role = excluded.role,
            text = excluded.text,
            created_at = excluded.created_at
        """,
        (conversation, node_id, message_id, parent_id, role, text, timestamp(created_at)),
    )


def upsert_memory(connection, account, source_id, source_file, kind, title, text, created_at=None):
    connection.execute(
        """
        INSERT INTO memories(account_id, source_id, source_file, kind, title, text, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(account_id, source_id) DO UPDATE SET
            source_file = excluded.source_file,
            kind = excluded.kind,
            title = excluded.title,
            text = excluded.text,
            created_at = excluded.created_at
        """,
        (account, source_id, str(source_file), kind, title, text, timestamp(created_at)),
    )
