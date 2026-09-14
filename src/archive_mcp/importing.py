from datetime import datetime


class ImportChanges:
    """Net content changes for identities touched by one atomic file import.

    Paths are provenance, not content. Keep only touched records in memory;
    no archive-wide scan, hash pass, or persistent revision copy is needed.
    """

    def __init__(self):
        self.records = {kind: {} for kind in ('conversations', 'nodes', 'memories')}
        self.protected_conversations = set()
        self.conversation_keys = {}

    def record(self, kind, key, before, after, protected=False):
        records = self.records[kind]
        original, _, earlier_protection = records.get(key, (before, before, False))
        records[key] = (original, after, protected or earlier_protection)

    def result(self, processed):
        summary = {}
        for kind, records in self.records.items():
            counts = dict(new=0, updated=0, unchanged=0, protected=0, removed=0)
            for before, after, protected in records.values():
                if before is None and after is None:
                    continue
                if before is None:
                    state = 'new'
                elif after is None:
                    state = 'removed'
                elif before != after:
                    state = 'updated'
                else:
                    state = 'protected' if protected else 'unchanged'
                counts[state] += 1
            summary[kind] = counts
        return {**processed, 'changes': summary}


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
    kind="conversation", *, changes=None, revision_check=True,
):
    before = connection.execute(
        "SELECT id, kind, title, created_at, updated_at, source_file FROM conversations "
        "WHERE account_id = ? AND source_id = ?", (account, source_id),
    ).fetchone()
    incoming = (kind, title, timestamp(created_at), timestamp(updated_at))
    old = tuple(before)[1:5] if before else None
    protected = bool(revision_check and before and before['updated_at'] is not None and (
        incoming[3] is None or incoming[3] < before['updated_at']
    ))
    if before is None:
        key = connection.execute(
            "INSERT INTO conversations(account_id, source_id, source_file, kind, title, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (account, source_id, str(source_file), *incoming),
        ).lastrowid
    else:
        key = before['id']
        if not protected and (old != incoming or before['source_file'] != str(source_file)):
            connection.execute(
                "UPDATE conversations SET kind = ?, title = ?, created_at = ?, updated_at = ?, "
                "source_file = ? WHERE id = ?", (*incoming, str(source_file), key),
            )
    if changes is not None:
        changes.conversation_keys[key] = (account, source_id)
        if protected:
            changes.protected_conversations.add(key)
        else:
            changes.protected_conversations.discard(key)
        changes.record('conversations', (account, source_id), old,
                       old if protected else incoming, protected and old != incoming)
    return key


def upsert_message(connection, conversation, node_id, message_id, parent_id, role, text, created_at, *, changes=None):
    before = connection.execute(
        "SELECT message_source_id, parent_source_id, role, text, created_at FROM messages "
        "WHERE conversation_id = ? AND node_source_id = ?", (conversation, node_id),
    ).fetchone()
    old = tuple(before) if before else None
    incoming = (message_id, parent_id, role, text, timestamp(created_at))
    protected = changes is not None and conversation in changes.protected_conversations
    if before is None:
        connection.execute(
            "INSERT INTO messages(conversation_id, node_source_id, message_source_id, parent_source_id, role, text, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)", (conversation, node_id, *incoming),
        )
    elif not protected and old != incoming:
        connection.execute(
            "UPDATE messages SET message_source_id = ?, parent_source_id = ?, role = ?, text = ?, created_at = ? "
            "WHERE conversation_id = ? AND node_source_id = ?", (*incoming, conversation, node_id),
        )
    if changes is not None:
        changes.record('nodes', (*changes.conversation_keys[conversation], node_id), old,
                       old if protected and before else incoming,
                       protected and before is not None and old != incoming)


def upsert_memory(connection, account, source_id, source_file, kind, title, text, created_at=None, *, changes=None):
    before = connection.execute(
        "SELECT kind, title, text, created_at, source_file FROM memories "
        "WHERE account_id = ? AND source_id = ?", (account, source_id),
    ).fetchone()
    old = tuple(before)[:4] if before else None
    incoming = (kind, title, text, timestamp(created_at))
    if before is None:
        connection.execute(
            "INSERT INTO memories(account_id, source_id, source_file, kind, title, text, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)", (account, source_id, str(source_file), *incoming),
        )
    elif old != incoming or before['source_file'] != str(source_file):
        connection.execute(
            "UPDATE memories SET kind = ?, title = ?, text = ?, created_at = ?, source_file = ? "
            "WHERE account_id = ? AND source_id = ?", (*incoming, str(source_file), account, source_id),
        )
    if changes is not None:
        changes.record('memories', (account, source_id), old, incoming)


def prune_messages(connection, conversation, retained, changes):
    """Remove parser-excluded derived nodes only from an accepted snapshot."""
    if conversation in changes.protected_conversations:
        return
    for row in connection.execute('SELECT id, node_source_id FROM messages WHERE conversation_id = ?', (conversation,)).fetchall():
        if row['node_source_id'] in retained:
            continue
        old = tuple(connection.execute(
            'SELECT message_source_id, parent_source_id, role, text, created_at FROM messages WHERE id = ?',
            (row['id'],),
        ).fetchone())
        changes.record('nodes', (*changes.conversation_keys[conversation], row['node_source_id']), old, None)
        connection.execute('DELETE FROM messages WHERE id = ?', (row['id'],))


def delete_conversation(connection, row, changes):
    """Account for an explicit adapter snapshot removal, including its nodes."""
    key = row['id']
    changes.conversation_keys[key] = (row['account_id'], row['source_id'])
    # Explicit whole-session exclusions/replacements override revision protection.
    changes.protected_conversations.discard(key)
    prune_messages(connection, key, set(), changes)
    old = tuple(row[field] for field in ('kind', 'title', 'created_at', 'updated_at'))
    changes.record('conversations', (row['account_id'], row['source_id']), old, None)
    connection.execute('DELETE FROM conversations WHERE id = ?', (key,))
