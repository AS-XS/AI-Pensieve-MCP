# Retrieval evaluation

Run the small synthetic baseline with:

```sh
make evaluate
```

Without Make, run `PYTHONPATH=src .venv/bin/python -m archive_mcp.evaluate`.
On Windows PowerShell, set `$env:PYTHONPATH = (Resolve-Path src).Path` and run
`.\.venv\Scripts\python.exe -m archive_mcp.evaluate`.

The command creates and removes a temporary synthetic database, then evaluates
search through a read-only connection. It needs no model or network service and
does not open or refresh the personal archive. The corpus contains 18 invented
messages and saved-context records, including unrelated distractors.

Each of the 11 cases pairs an everyday question with an explicitly chosen FTS5
query and expected source identities. The question is explanatory: no model
converts it into a query. This measures retrieval for those queries, not an AI
client's ability to understand natural language or synthesize a correct answer.

## Current baseline

At five results per query:

| Measure | Result |
| --- | --- |
| Positive questions with a relevant result | 9 / 10 |
| Mean reciprocal rank | 0.90 |
| Mean recall of labeled relevant records | 0.90 |
| Negative questions correctly returning no results | 1 / 1 |

The successful cases cover a storage decision, a date-filtered revision,
comparison of two decisions, cross-provider evidence, an alternate branch,
saved context, a decision beyond the first 4,000 characters, and account/provider
isolation, plus title-only lookup. Their first relevant result appears at rank
one. The initial body-only baseline found 8 of 10 positive cases; title search
adds case 10 without losing any previously successful case.

The remaining deliberate miss is:

- Case 9 asks about operating “disconnected,” while the relevant source says
  “offline.” Exact keyword search does not connect these words.

Case 10 searches for “Orchid,” which appears only in the conversation title.
It now returns the matching conversation. Its gold label identifies that
conversation instead of the individual message used before title retrieval
existed. A follow-up retrieval test confirms the conversation contains the
original next-step message (`milestone`).

These are a repeatable baseline, not a claim of 90% accuracy on a personal
archive. The corpus is small, the queries are hand-written, and the missed cases
were deliberately chosen to expose known limitations. Keep the cases when
improving search and update their baseline expectations as behavior improves.

The synonym case alone does not justify adding an embedding model: first measure realistic
personal queries and try ordinary query reformulation.

## Continuous integration

The four Ubuntu/Windows and Python 3.10/3.13 jobs run this synthetic evaluation.
CI prints the result and requires all eleven cases to be present. Every case
except the documented synonym miss (case 9) must pass with full recall; case 9
may improve. This check is separate from the evaluator's exit code, which treats
retrieval misses as valid measurement outcomes.

## Evaluate a private archive

Keep private cases inside ignored `runtime/`, for example
`runtime/retrieval-cases.json`. Follow the structure in
[`fixtures/retrieval_cases.json`](../fixtures/retrieval_cases.json):

```json
[
  {
    "question": "What storage did we choose for the archive?",
    "query": "archive AND SQLite",
    "filters": {"providers": ["chatgpt"], "accounts": ["personal"]},
    "expected": [
      {
        "record_type": "message",
        "provider": "chatgpt",
        "account": "personal",
        "conversation_id": "REPLACE_WITH_SOURCE_CONVERSATION_ID",
        "record_id": "REPLACE_WITH_SOURCE_NODE_ID"
      }
    ]
  }
]
```

Choose questions and independently confirm the expected evidence before tuning
queries. Use source IDs, not SQLite row numbers. Memory labels use
`record_type: "memory"`, a null `conversation_id`, and the source memory ID.
Conversation-title labels use `record_type: "conversation"` with both
`record_id` and `conversation_id` set to the source conversation ID. A title
hit locates the container; the client still needs to retrieve its messages.
Use `expected: []` only when no results are appropriate. Filters support
`providers`, `accounts`, `date_from`, and `date_to`, with dates as ISO strings.

```sh
PYTHONPATH=src .venv/bin/python -m archive_mcp.evaluate \
  --database runtime/archive.sqlite \
  --cases runtime/retrieval-cases.json --limit 5
```

The database opens read-only. Output includes only case numbers, counts, ranks,
and scores; it omits questions, queries, source IDs, paths, and returned text.
An expected record that does not exist is an input error, not a retrieval miss.
Search misses are normal evaluation outcomes and do not make the command fail;
execution/input-file failures exit with code 2 and a safe exception class.
Argument-parsing failures instead print argparse usage and may echo arguments.

For positive cases, `passed` means at least one expected record was found.
`recall` measures how many labeled records were found, so a comparison question
can pass while still missing part of its evidence. Mean reciprocal rank uses
the first relevant result, with zero for misses. Negative cases are reported
separately. Unlabeled results are not scored for relevance; this is not a
precision or answer-quality evaluation.

## Grouped retrieval verification

The synthetic scores above still describe individual-result search.
`search_conversations` adds a separate presentation of the first 50 candidates
as distinct conversation groups, with up to three matching snippets each.
`get_conversation_matches` expands a group into paginated title/message hits.

Synthetic tests cover a busy thread hiding other conversations, identical
source IDs across accounts/providers, separate saved memories, combined title
and body matches, date-filter replay, and expansion beyond the global
candidate limit. A private evaluation can compare frozen expected conversation
identities with `groups[*]` and then verify that each group's `matches` leads
to the expected evidence. Keep those cases and results in ignored runtime
files; group discovery is distinct from exact-message or answer-quality scoring.

## Continuation verification

The automated suite separately checks exact reconstruction of long messages,
Unicode and embedded null characters, page boundaries, alternate branches,
identity isolation, MCP parameter limits, and privacy-safe logging.

The local development log records an additional private continuation check on
2026-09-04. That was a historical measurement of that archive snapshot, not
part of this repeatable synthetic baseline or a current completeness guarantee.
The automated STDIO tests verify retrieval using synthetic data. No private
message text is part of the synthetic corpus or public report.
