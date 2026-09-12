"""Round-robin archive reading with resumable source coverage."""

import json
import time

from .sweep import sweep_archive


def survey_archive(connection, cursor=None, providers=None, accounts=None,
                   date_from=None, date_to=None, max_records=50, max_chars=12000):
    if not 1 <= max_records <= 50 or not 1 <= max_chars <= 16000:
        raise ValueError("Invalid survey page budget")
    scope = [sorted(set(providers or [])), sorted(set(accounts or [])), date_from, date_to]
    if cursor is None:
        clauses, values = [], []
        for field, selected in (("provider", scope[0]), ("label", scope[1])):
            if selected:
                clauses.append(f"{field} IN ({','.join('?' for _ in selected)})")
                values.extend(selected)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        rows = connection.execute(
            "SELECT provider, label FROM source_accounts" + where + " ORDER BY provider, label LIMIT 51", values)
        sources = [dict(provider=p, account=a, cursor=None, status="unexamined",
                        records_completed=0, characters_read=0) for p, a in rows]
        if len(sources) > 50:
            raise ValueError("Select at most 50 source accounts per survey")
        state = dict(version=1, scope=scope, sources=sources, turn=0, pages=0)
    else:
        try:
            if not cursor.startswith("survey:"):
                raise ValueError
            state = json.loads(cursor[7:])
            sources = state["sources"]
            if (state["version"] != 1 or state["scope"] != scope or
                    not isinstance(sources, list) or not 1 <= len(sources) <= 50 or
                    type(state["turn"]) is not int or not 0 <= state["turn"] < len(sources) or
                    type(state["pages"]) is not int or state["pages"] < 0):
                raise ValueError
            for source in sources:
                if (source["status"] not in ("unexamined", "partial", "complete") or
                        not isinstance(source["provider"], str) or not isinstance(source["account"], str) or
                        any(type(source[k]) is not int or source[k] < 0
                            for k in ("records_completed", "characters_read")) or
                        source["cursor"] is not None and not isinstance(source["cursor"], str)):
                    raise ValueError
        except (AttributeError, KeyError, TypeError, ValueError):
            raise ValueError("Invalid survey cursor or changed filters; restart the survey") from None
    records, characters = [], 0
    deadline = time.monotonic() + 2
    stopped = "complete"
    while any(s["status"] != "complete" for s in sources):
        if len(records) >= max_records or characters >= max_chars:
            stopped = "page_budget"
            break
        if time.monotonic() >= deadline:
            stopped = "time_budget"
            break
        source = sources[state["turn"]]
        if source["status"] == "complete":
            state["turn"] = (state["turn"] + 1) % len(sources)
            continue
        try:
            page = sweep_archive(
                connection, source["cursor"], [source["provider"]], [source["account"]],
                date_from, date_to, min(5, max_records - len(records)), min(1000, max_chars - characters),
            )
        except TimeoutError:
            stopped = "time_budget"
            break
        records.extend(page["records"])
        characters += page["characters_returned"]
        source["cursor"] = page["next_cursor"]
        source["status"] = "partial" if page["has_more"] else "complete"
        source["records_completed"] += page["records_completed"]
        source["characters_read"] += page["characters_returned"]
        state["turn"] = (state["turn"] + 1) % len(sources)
    complete = all(s["status"] == "complete" for s in sources)
    state["pages"] += 1
    return {
        "records": records, "characters_returned": characters,
        "pages_read": state["pages"], "complete": complete,
        "next_cursor": None if complete else "survey:" + json.dumps(state, separators=(",", ":")),
        "stop_reason": "complete" if complete else stopped,
        "sources": [{k: v for k, v in s.items() if k != "cursor"} for s in sources],
        "coverage_note": "Source-balanced sequential reading, not representative sampling. "
                         "Complete means all eligible text in the selected imported scope was read. "
                         "Restart after imports, refreshes, rebuilds, or database changes.",
    }
