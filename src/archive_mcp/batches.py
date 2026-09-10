import time
from collections import Counter

from .db import initialize


def run_batch(connection, sources, account, mode, candidates=None, ignored=()):
    sources = list(sources)
    ignored = list(ignored)
    candidate_count = (
        candidates if candidates is not None else len(sources) + len(ignored)
    )
    initialize(connection)

    with connection:
        batch_id = connection.execute(
            """
            INSERT INTO import_batches(
                mode, account, started_at, status, candidate_files
            ) VALUES (?, ?, ?, 'running', ?)
            """,
            (mode, account, time.time(), candidate_count),
        ).lastrowid

    totals = Counter(files=0, candidate_files=candidate_count)
    formats = Counter(kind for kind, _, _ in sources)
    warnings = [(None, "unrecognized_format", "") for _ in ignored]

    try:
        for kind, path, importer in sources:
            result = importer(connection, path, account)
            totals["files"] += 1
            totals.update(result)
            if result.get("excluded_review_sessions"):
                warnings.append((kind, "excluded_review_session", ""))
            if not result.get("nodes") and not result.get("memories"):
                warnings.append((kind, "no_indexable_records", ""))
    except Exception as error:
        warnings.append((kind, "import_failed", type(error).__name__))
        finish(connection, batch_id, "failed", totals["files"], warnings)
        raise

    finish(connection, batch_id, "completed", totals["files"], warnings)
    return {
        "batch_id": batch_id,
        **dict(totals),
        "ignored_files": len(ignored),
        "formats": dict(sorted(formats.items())),
        "warnings": dict(sorted(
            Counter(code for _, code, _ in warnings).items()
        )),
    }


def finish(connection, batch_id, status, imported_files, warnings):
    with connection:
        connection.executemany(
            """
            INSERT INTO import_warnings(
                batch_id, source_format, code, detail
            ) VALUES (?, ?, ?, ?)
            """,
            [
                (batch_id, kind, code, detail)
                for kind, code, detail in warnings
            ],
        )
        connection.execute(
            """
            UPDATE import_batches SET
                completed_at = ?, status = ?, imported_files = ?, warning_count = ?
            WHERE id = ?
            """,
            (time.time(), status, imported_files, len(warnings), batch_id),
        )


def import_report(connection, limit=10):
    initialize(connection)
    batches = [dict(row) for row in connection.execute(
        """
        SELECT id, mode, status, candidate_files, imported_files, warning_count
        FROM import_batches ORDER BY id DESC LIMIT ?
        """,
        (max(1, min(limit, 50)),),
    )]
    for batch in batches:
        batch["warnings"] = dict(connection.execute(
            """
            SELECT code, count(*) FROM import_warnings
            WHERE batch_id = ? GROUP BY code ORDER BY code
            """,
            (batch["id"],),
        ))
    return batches
