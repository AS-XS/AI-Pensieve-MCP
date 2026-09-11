"""Stateless, budgeted reading of messages and saved context without keywords."""

import json
import sqlite3
import time

from .db import filters, iso_time


def sweep_archive(connection, cursor=None, providers=None, accounts=None,
                  date_from=None, date_to=None, max_records=20, max_chars=12000):
    if not 1 <= max_records <= 50 or not 1 <= max_chars <= 16000:
        raise ValueError("Invalid sweep budget.")
    scope = [sorted(set(providers or [])), sorted(set(accounts or [])), date_from, date_to]
    phase, row_id, offset = 0, 0, 0
    if cursor is not None:
        try:
            if not cursor.startswith("sweep:"):
                raise ValueError
            version, phase, row_id, offset, saved_scope = json.loads(cursor[6:])
            if (version != 1 or saved_scope != scope or
                    any(type(v) is not int for v in (phase, row_id, offset)) or
                    phase not in (0, 1) or row_id < 0 or offset < 0):
                raise ValueError
        except (AttributeError, TypeError, ValueError):
            raise ValueError("Invalid sweep cursor or changed filters; restart the sweep.") from None

    records = []
    characters = 0
    deadline = time.monotonic() + 2
    next_cursor = None
    connection.set_progress_handler(lambda: time.monotonic() >= deadline, 1000)
    try:
        while phase < 2:
            if time.monotonic() >= deadline:
                raise TimeoutError("Sweep time budget exceeded; retry with narrower filters.")
            clauses, values = filters(providers, accounts, date_from, date_to, "m.created_at")
            if phase == 0:
                columns = """m.node_source_id AS record_id, m.parent_source_id,
                    m.role, c.source_id AS conversation_id, c.kind AS kind, c.title"""
                tables = """messages m JOIN conversations c ON c.id = m.conversation_id
                    JOIN source_accounts a ON a.id = c.account_id"""
                clauses += " AND m.text != ''"
            else:
                columns = """m.source_id AS record_id, NULL AS parent_source_id,
                    NULL AS role, NULL AS conversation_id, m.kind, m.title"""
                tables = "memories m JOIN source_accounts a ON a.id = m.account_id"
            row = connection.execute(
                f"""SELECT m.id, m.text, m.created_at, a.provider, a.label AS account,
                    {columns} FROM {tables} WHERE m.id >= ?{clauses}
                    ORDER BY m.id LIMIT 1""", (row_id, *values),
            ).fetchone()
            if row is None:
                phase, row_id, offset = phase + 1, 0, 0
                continue
            if time.monotonic() >= deadline:
                raise TimeoutError("Sweep time budget exceeded; retry with narrower filters.")
            if row["id"] != row_id:
                row_id, offset = row["id"], 0
            if len(records) == max_records or characters == max_chars:
                next_cursor = "sweep:" + json.dumps([1, phase, row_id, offset, scope], separators=(",", ":"))
                break
            text = row["text"]
            if offset > len(text):
                raise ValueError("Sweep cursor no longer matches; restart the sweep.")
            chunk = text[offset:offset + max_chars - characters]
            end = offset + len(chunk)
            record = {key: row[key] for key in (
                "provider", "account", "record_id", "conversation_id", "kind",
                "parent_source_id", "role",
            )}
            record.update(record_type="message" if phase == 0 else "memory",
                          title=row["title"][:200], created_at=iso_time(row["created_at"]),
                          text=chunk, offset=offset, total_chars=len(text),
                          record_complete=end == len(text))
            records.append(record)
            characters += len(chunk)
            row_id, offset = (row_id + 1, 0) if end == len(text) else (row_id, end)
    except sqlite3.OperationalError as error:
        if str(error) == "interrupted":
            raise TimeoutError("Sweep time budget exceeded; retry with narrower filters.") from None
        raise
    finally:
        connection.set_progress_handler(None, 0)
    return {
        "records": records, "characters_returned": characters,
        "records_completed": sum(r["record_complete"] for r in records),
        "sources_in_page": [dict(provider=p, account=a) for p, a in sorted(
            {(r["provider"], r["account"]) for r in records})],
        "next_cursor": next_cursor, "has_more": next_cursor is not None,
        "remaining_scope_exhausted": next_cursor is None,
        "order": "messages_then_saved_context_by_local_id",
        "freshness_policy": "restart_after_import_refresh_or_rebuild",
        "coverage_note": "Only a traversal from the start through all pages covers the selected scope. "
                         "Empty message nodes and conversations without text are excluded. "
                         "This is sequential reading, not representative sampling.",
    }
