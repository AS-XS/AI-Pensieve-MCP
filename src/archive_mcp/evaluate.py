"""Small, local retrieval evaluation; reports never include queries or source IDs."""

import argparse
import json
import tempfile
from contextlib import closing
from pathlib import Path

from .db import connect, initialize, search, timestamp
from .importing import account_id, conversation_id, upsert_memory, upsert_message


IDENTITY = ("record_type", "provider", "account", "conversation_id", "record_id")
FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


def seed_corpus(connection, records):
    """Load only the deliberately synthetic retrieval corpus."""
    initialize(connection)
    with connection:
        for record in records:
            account = account_id(connection, record["provider"], record["account"])
            if record["record_type"] == "memory":
                upsert_memory(
                    connection, account, record["record_id"], "synthetic",
                    "saved_context", record["title"], record["text"], record["created_at"],
                )
            else:
                conversation = conversation_id(
                    connection, account, record["conversation_id"], "synthetic",
                    record["title"], record["created_at"], record["created_at"],
                )
                upsert_message(
                    connection, conversation, record["record_id"], record["record_id"],
                    record.get("parent_source_id"), record.get("role", "assistant"),
                    record["text"], record["created_at"],
                )


def evaluate(connection, cases, limit=5):
    if not cases or not 1 <= limit <= 50:
        raise ValueError("Supply at least one case and a limit between 1 and 50")
    outcomes = []
    for number, case in enumerate(cases, 1):
        expected = {tuple(record[key] for key in IDENTITY) for record in case["expected"]}
        # Catch stale or mistyped gold labels before reporting a search miss.
        for kind, provider, account, conversation, record in expected:
            if kind == "message":
                present = connection.execute(
                    """SELECT 1 FROM messages m
                    JOIN conversations c ON c.id = m.conversation_id
                    JOIN source_accounts a ON a.id = c.account_id
                    WHERE a.provider = ? AND a.label = ? AND c.source_id = ?
                      AND m.node_source_id = ?""",
                    (provider, account, conversation, record),
                ).fetchone()
            elif kind == "conversation" and conversation == record:
                present = connection.execute(
                    """SELECT 1 FROM conversations c
                    JOIN source_accounts a ON a.id = c.account_id
                    WHERE a.provider = ? AND a.label = ? AND c.source_id = ?""",
                    (provider, account, conversation),
                ).fetchone()
            elif kind == "memory" and conversation is None:
                present = connection.execute(
                    """SELECT 1 FROM memories m
                    JOIN source_accounts a ON a.id = m.account_id
                    WHERE a.provider = ? AND a.label = ? AND m.source_id = ?""",
                    (provider, account, record),
                ).fetchone()
            else:
                present = None
            if present is None:
                raise ValueError(f"Case {number}: expected record does not exist")
        filters = dict(case.get("filters", {}))
        for field in ("date_from", "date_to"):
            if field in filters:
                filters[field] = timestamp(filters[field], end=field == "date_to")
        try:
            results = search(connection, case["query"], limit=limit, **filters)
        except Exception:
            raise ValueError(f"Case {number}: search failed") from None
        found = [tuple(record[key] for key in IDENTITY) for record in results]
        ranks = [rank for rank, identity in enumerate(found, 1) if identity in expected]
        outcomes.append({
            "case": number,
            "expected_count": len(expected),
            "result_count": len(found),
            "first_relevant_rank": min(ranks) if ranks else None,
            "recall": len(expected.intersection(found)) / len(expected) if expected else None,
            "passed": bool(ranks) if expected else not found,
        })
    positives = [case for case in outcomes if case["expected_count"]]
    negatives = [case for case in outcomes if not case["expected_count"]]
    return {
        "top_k": limit,
        "case_count": len(outcomes),
        "positive_cases": len(positives),
        "hit_rate": sum(case["passed"] for case in positives) / len(positives) if positives else None,
        "mean_reciprocal_rank": sum(
            1 / case["first_relevant_rank"] if case["first_relevant_rank"] else 0
            for case in positives
        ) / len(positives) if positives else None,
        "mean_recall": sum(case["recall"] for case in positives) / len(positives) if positives else None,
        "negative_cases": len(negatives),
        "correct_empty_results": sum(case["passed"] for case in negatives),
        "cases": outcomes,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path)
    parser.add_argument("--cases", type=Path)
    parser.add_argument("--limit", type=int, default=5, choices=range(1, 51))
    args = parser.parse_args(argv)
    if bool(args.database) != bool(args.cases):
        parser.error("--database and --cases must be supplied together")
    try:
        cases = json.loads((args.cases or FIXTURES / "retrieval_cases.json").read_text())
        if args.database:
            with closing(connect(args.database, read_only=True)) as connection:
                result = evaluate(connection, cases, args.limit)
        else:
            with tempfile.TemporaryDirectory() as directory:
                database = Path(directory) / "evaluation.sqlite"
                with closing(connect(database)) as connection:
                    seed_corpus(connection, json.loads((FIXTURES / "retrieval_corpus.json").read_text()))
                with closing(connect(database, read_only=True)) as connection:
                    result = evaluate(connection, cases, args.limit)
    except Exception as error:
        # Input paths and query text can be private; retain only the safe class.
        parser.exit(2, f"Evaluation failed ({type(error).__name__})\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
