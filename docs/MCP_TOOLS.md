# MCP tools and technical details

This document describes the local MCP interface for contributors and users who
want to troubleshoot or automate the archive. The main README intentionally
keeps these details out of the first-run path.

## Normal retrieval flow

Use `archive_status` or `list_sources` when you need to establish the available
sources. Choose a retrieval tool for the question: `search_conversations` finds
distinct discussions, `cross_reference` searches separately across sources,
and `search_history` returns individual ranked matches. Use `list_conversations`
to page titles and metadata without keywords. These are alternative starting
points; a request does not need to call every tool.

Expand a relevant group with `get_conversation_matches`, or read its evidence
with `get_conversation`, `get_message_context`, or `get_memory`. Use `get_message`
for exact message text, including continuation after a truncated preview.
Search results and the `matches` inside groups provide stable identifiers for
the next call:

- A message result's `conversation_id` and `record_id` become
  `conversation_id` and `message_id` for `get_message_context`.
- A memory result's `record_id` becomes `memory_id` for `get_memory`.
- A conversation result's `conversation_id` plus its provider and account become
  the lookup key for `get_conversation`.

## Tool reference

| Tool | Purpose | Main inputs |
| --- | --- | --- |
| `archive_status` | Aggregate providers, accounts, record kinds, counts, and date ranges. | none |
| `list_sources` | Filter those source summaries by provider or account. | `provider?`, `account?` |
| `list_conversations` | Page conversations without requiring a keyword match; restart after imports/refreshes. | provider/account/date filters, `cursor`, `limit` |
| `cross_reference` | Search each selected provider/account separately, with evidence and coverage limits. | `query`, provider/account/date filters, per-source `candidate_limit`, source `limit` |
| `search_history` | Search message text, saved context, and conversation titles with SQLite FTS5. | `query`, provider/account/date filters, `limit` |
| `search_conversations` | Show distinct conversations with matching snippets; saved memories remain separate. | `query`, provider/account/date filters, group `limit` |
| `get_conversation_matches` | Expand one conversation into paginated ranked title/message matches. | `query`, provider, account, conversation ID, date filters, `offset`, `limit` |
| `get_conversation` | Read a conversation page; optionally check newest messages first. | provider, account, conversation ID, `offset`, `limit`, `newest_first` |
| `get_message_context` | Read one message with graph-aware ancestors and descendants, including branches. | provider, account, conversation ID, message ID, `before`, `after` |
| `get_message` | Read exact message text in bounded character pages. | provider, account, conversation ID, message ID, `offset`, `limit` |
| `get_memory` | Read one saved memory or context record. | provider, account, memory ID |
| `sweep_archive` | Read messages and saved context without keywords under a page budget. | source/date filters, `cursor`, `max_records`, `max_chars` |
| `survey_archive` | Rotate across provider/accounts with cumulative coverage and resumable text slices. | source/date filters, `cursor`, `max_records`, `max_chars` |

The additional `sweep_archive` tool reads bounded text pages without keywords,
including saved context. See [archive sweep](ARCHIVE_SWEEP.md) for its arguments,
continuation, budgets, and coverage contract.

All thirteen tools are read-only. They do not import, edit, delete, or re-index data.

Search/enumeration filters use plural `providers` and `accounts` lists.
`list_sources` and direct record lookups instead use singular `provider` and
`account` strings. Omitting a list or passing an empty list leaves it unfiltered.
The CLI uses repeatable `--provider`/`--account` options for list filters.

The MCP layer removes the stored `source_file` provenance field from responses,
because it can contain a local path. Provenance remains available inside the
local SQLite database for import diagnostics.

## Limits and search syntax

- Search and conversation pages are limited to 50 results.
- Message and memory previews contain at most 4,000 source characters, followed
  by an ellipsis when `truncated` is true. Exact `get_message` pages contain at
  most 4,000 characters and never add an ellipsis.
  `get_message` cannot retrieve the remainder of a truncated `get_memory`
  result; `sweep_archive` can read complete saved-context text across pages.
- Message context accepts up to 10 ancestors and 10 descendant levels, with a
  maximum of 50 returned descendants.
- `search_history` accepts SQLite FTS5 syntax, including quoted phrases,
  Boolean operators, and prefixes such as `search*`.
- Provider, account, and date filters are applied before the result limit.

Search snippets use FTS5's 12-token window, not the 4,000-character preview cap.
Titles, IDs, source listings, and total response bytes have no fixed character
budget. Context returns up to 10 visible ancestors (possibly traversing more
empty nodes); descendant reads have a 50-row cap per level as well as a
50-visible-descendant total. It is a bounded view, with no completeness flag.
Conversation pages default to stored row order and omit empty-text nodes.
With `newest_first=true`, they sort by timestamp descending, then local row ID
descending, with undated messages last. `undated_messages` reports the number
that cannot be placed chronologically. This includes all branches and independent
roots; it does not infer that later messages supersede earlier branches. Keep
the same order while paging. Check other conversations for project updates too.

## Optional discovery prompt

The server also exposes an MCP prompt named `discover_history`, with a required
`question` string. It supplies a reusable guide: inventory, two distinct search
queries, one small balanced survey, original evidence, and recent project updates.
Retrieving the prompt performs no archive read and consumes no server read budget.
It does not add another tool, run a model, or force the client to follow the guide.

Prompt discovery/retrieval is verified with the Python MCP SDK. Availability and
selection in individual AI applications have not been verified. Clients that
support MCP prompts can request `discover_history`; custom Python clients can
use `client.get_prompt("discover_history", {"question": "What work could I revisit?"})`.

## Client-calculated coverage

Custom Python clients can use `archive_mcp.client_coverage.CoverageLedger` for
one task against one unchanged archive. Feed each structured result once:

```python
ledger = CoverageLedger()
result = await client.call_tool(tool_name, arguments)
ledger.record(tool_name, arguments, result.structured_content, failed=result.is_error)
coverage = ledger.summary()
```

Import the class from `archive_mcp.client_coverage`. If a request is rejected
before a result is returned, record it with `failed=True`; record interrupted
attempts with `unfinished=True`. The helper distinguishes attempts from successful
results and separates searched sources, sources with returned text, and complete
traversal. It copies inventory totals directly and holds counters/source identities
and traversal cursors in memory, without retaining retrieved text or writing files.
Text counts include `text`/`snippet` fields, including title snippets and repeated reads.

Full-archive traversal is established conservatively by an unfiltered sweep or
survey followed from its first page through an unbroken cursor chain. A tail page,
date-filtered traversal, or search with no matches does not establish full coverage.
The helper does not check database freshness: create a fresh ledger after imports,
refreshes, rebuilds, or other archive changes. Unknown inventory is reported explicitly.

This integration is available to custom clients and the optional evaluation runner;
it does not automatically change other AI applications' answers or accounting.
Display its calculated coverage separately from the model's claims. Valid counts
do not establish accurate interpretation or complete provider exports.

## Optional process read budgets

For a dedicated bounded task, start the STDIO server with optional
`--max-read-calls`, `--max-read-chars`, and `--max-read-seconds` arguments.
All default to unlimited; ordinary long-running client registrations are unchanged.
For example, append `--max-read-calls 12 --max-read-chars 24000 --max-read-seconds 90`
to the existing server command for a temporary survey session.

The server counts valid calls entering its read handler, including failed reads.
It refuses further archive reads after the call limit. Time starts on the first
read and is checked before reading and before releasing a result; it is not a
hard interrupt of every SQL query or a bound on model generation time. Character
limits count returned `text` and `snippet` fields, including repeated reads,
not metadata, serialized JSON, or model tokens. An oversized response is withheld
and consumes a call; request a smaller page if allowance remains.

With limits enabled, dictionary responses include `read_budget` with used and
remaining counts. List responses keep their existing shape; the same budget
still applies. Accounting is serialized for concurrent requests. State is held
in this server process only and resets on restart. No archive table is written.

These limits bound reads/output from this one server process. They do not stop
a client from attempting more calls, calling another tool/server, or starting a
new process. Configure them for a dedicated task, not a shared permanent server
unless that process-wide lifetime is intended. Survey pagination itself has
per-page limits; it does not automatically enable a whole-task budget.

## Bounded conversation enumeration

`list_conversations` is the coverage primitive for sweeps and later
cross-reference workflows. It returns conversation titles, provider/account,
kind, dates, and message counts without message text. Start at `cursor: 0`, then
pass each returned `next_cursor` with unchanged filters. A null `next_cursor`
means there are no more conversations in that traversal.

Enumeration date filters use conversation creation time. To find newer messages
inside an older conversation, use a search tool with message date filters.

The default and maximum page size is 50. Filters are applied before the page
limit. The response declares `freshness_policy:
"restart_after_import_refresh_or_rebuild"`. Complete a traversal while the
archive is unchanged. Restart at cursor 0 after any import or refresh (including
a failed attempt), rebuild, database switch, or filter change. Calls read current
data independently; there is no held snapshot or automatic change detection.
Rows can change or their local IDs can be reused. The earlier experimental
`snapshot_max_id` parameter was removed because it could not guarantee a snapshot.

`cross_reference` is the comparison primitive for questions that span sources.
It selects up to `limit` sources (default 10, maximum 50), in provider/account
order after source filters, then runs a separate ranked search for each source.
`candidate_limit` applies **per source** (default 50, maximum 200). A busy source
cannot consume another selected source's candidate allowance. Dates filter
matching evidence, not the source inventory.

Each selected source gets a bundle, including `status: "no_matches"` when its
query/date filters find nothing. `sources_available`, `sources_examined`, and
`sources_unexamined` distinguish searched sources from those skipped by `limit`.
Use `list_sources` and narrower provider/account filters to inspect skipped
sources. A skipped source is not evidence of an absence of matches.

Each bundle includes up to five ranked evidence records, conversation IDs/dates,
`matched_records` within its candidate pool, `candidate_limit_reached`, and
`evidence_omitted` within that pool. Each evidence item repeats source provenance
and stable IDs. Totals report `candidates_examined`, `candidate_limit_scope:
"per_source"`, and whether any source reached its candidate limit. At most
`limit * candidate_limit` candidate records are collected, with at most
`5 * limit` evidence snippets. These are record limits, not time or character
budgets. A reached limit means additional matches may exist. Conversation counts
and dates describe the retrieved candidates, not complete historical coverage.

Use `get_message` for message evidence (`record_id` is its `message_id`),
`get_memory` for saved context (`record_id` is its `memory_id`), and
`get_conversation` for title matches. Include the returned provider/account and,
for conversations/messages, conversation ID. Matches show archived evidence;
they do not by themselves establish that different sources independently agree.

## Conversation-title search

The same query searches message bodies, saved-context bodies, and conversation
titles. Title matches have `record_type: "conversation"` and
`matched_field: "title"`; body matches have `matched_field: "text"`. The title
snippet highlights the matching words. A conversation contributes one title
result, regardless of how many messages it contains.

Use the title result's provider, account, and `conversation_id` with
`get_conversation` to read its messages. Its `record_id` is the conversation ID,
not a message ID. Title results have null role and parent-message fields and
retain the conversation kind, including local sessions and inferred sessions.

Date filters use the conversation's **creation time** for title matches and
the individual record's timestamp for message or saved-context matches.
Undated records do not match a date filter. A newer message in an older thread
can therefore match a date range even when that thread's title does not.

All matches share the same result limit and are sorted by their index's BM25
score, with stable source identities breaking ties. This is a simple combined
ranking, not a calibrated relevance model. A matching title and matching
messages from the same conversation can both appear. A query must match within
one title or body; terms are not combined across the two fields.

## Grouped search and expansion

`search_conversations` applies the same query and filters as ordinary search,
reads its first 50 ranked candidates, and groups by provider, account, and
conversation ID. Title and message hits for one thread share a group. A saved
memory gets its own group identified by `memory_id`; separate memories are
never merged just because their conversation IDs are null.

Groups retain the order of their best match. Each contains up to three ranked
`matches`, with snippets, record types, message IDs, and ancestry metadata.
`limit` counts groups (default 10, maximum 50). The response also reports:

- `candidate_matches` per group: matches in the examined pool, not a total over
  the whole archive.
- `candidates_examined` and `candidate_limit`: the pool size and its cap of 50.
- `candidate_limit_reached`: the pool contains 50 records, so additional
  candidates may exist. This does not prove that more exist.
- `groups_omitted`: groups in that pool omitted by the requested group limit.

This is bounded grouping, not exhaustive conversation search. If one thread
occupies all 50 candidates, other threads can still be absent. Narrow the query
or apply provider/account/date filters when needed. There is no grouped-page
cursor beyond that candidate window.

To expand a conversation group, call `get_conversation_matches` with its
provider, account, conversation ID, and the **same query and date filters**.
Expansion searches that conversation directly and can retrieve matches beyond
the original 50-candidate window. Follow `next_offset` until null; each page
contains at most 50 ranked matches. An existing conversation with no matches
returns an empty page; an unknown identity returns a lookup error.

The expansion includes title and message hits, not unrelated saved memories.
Use each message's `record_id` with `get_message_context` or `get_message` to
read its evidence. Use `get_conversation` for a title result or for broader
context that does not contain the search words. Use `get_memory` for a saved
memory group. Branches keep their original message identities and ancestry.

Pagination reflects the database at each call. After a refresh or a change to
the query or filters, restart expansion at offset zero. This feature needs no
schema upgrade. Reconnect existing MCP processes to load the two new tools;
the server instructions recommend grouped search as the first retrieval step.

CLI equivalents (these deliberately display requested snippets):

```sh
PYTHONPATH=src .venv/bin/python -m archive_mcp search \
  runtime/archive.sqlite 'QUERY' --grouped --limit 5
PYTHONPATH=src .venv/bin/python -m archive_mcp get-conversation-matches \
  runtime/archive.sqlite PROVIDER ACCOUNT CONVERSATION_ID 'QUERY' \
  --offset 0 --limit 10

PYTHONPATH=src .venv/bin/python -m archive_mcp list-conversations \
  runtime/archive.sqlite --limit 50

PYTHONPATH=src .venv/bin/python -m archive_mcp cross-reference \
  runtime/archive.sqlite 'QUERY' --candidate-limit 50 --limit 10
```

Ordinary `search_history` and CLI search without `--grouped` retain their
individual-result shape and ranking.

## Archive status and schema

`archive_status` includes `schema_version` alongside counts and source/date
ranges. The current version is 1. It is informational; status does not migrate
or rebuild anything. The complete table and field mapping is in the
[schema guide](SCHEMA.md).

Status date ranges come from message and saved-context timestamps, not
conversation creation dates. Message counts include empty-text nodes, whereas
conversation reads omit them. `list_conversations` covers conversation rows
only: saved memories, projects, and notebook metadata are not enumerated.
Use `sweep_archive` for saved-context traversal and text continuation.

Status, enumeration, and cross-reference render dates as ISO UTC strings;
ordinary search and direct record reads return numeric Unix seconds or null.
Date-only upper filters include through 23:59:59.999 UTC. MCP integer arguments
are schema-validated; corresponding database helpers clamp limits and offsets.

Use the [data lifecycle guide](DATA_LIFECYCLE.md) for refresh semantics, fresh
rebuilds, removal limits, and optional external-drive snapshots.

## Upgrading an existing archive

After updating the code, run this once before reconnecting the MCP server:

```sh
PYTHONPATH=src .venv/bin/python -m archive_mcp init runtime/archive.sqlite
```

On Windows PowerShell, set `$env:PYTHONPATH = (Resolve-Path src).Path` and run
`.\.venv\Scripts\python.exe -m archive_mcp init runtime\archive.sqlite`.

For supported version-0 archives, initialization adds and backfills the title
index atomically, preserving existing records. Repeating it does not rebuild
an existing title index.
Normal imports also initialize the index when needed. Insert, title-update,
and delete triggers keep it in sync; `make check` validates all three FTS
indexes against their source records. MCP tools remain read-only and do not
perform this upgrade themselves.

Version 1 initialization returns immediately; it does not repair missing schema
objects. `import-report` also initializes the database, so unlike MCP/status it
can create or migrate one. `check` needs an initialized database and opens a
writable connection for rolled-back FTS integrity commands.

## Long message continuation

Use `get_message` with the provider, account, conversation ID, and a search
result's `record_id` or a message preview's `node_source_id`. Start at `offset: 0`.
The response includes exact `text`, `offset`, `next_offset`, and `total_chars`,
plus message identity, ancestry, role, and timestamp. Request `next_offset` to
continue; `null` means the message is finished. The default `limit` is 4,000;
smaller pages are allowed. Offsets count Unicode code points, not bytes.

Do not concatenate the old preview with these pages: previews may contain an
added ellipsis. Fetch exact pages from offset zero when assembling a complete
message. A request at or beyond the end returns empty text and a null next
offset. Provider, account, conversation, and message IDs must all match.

Conversation `offset` still counts messages; `get_message` offset counts
characters in just one message. Branches remain separate. Saved memories keep
their existing preview limit; this continuation tool reads conversation and
session messages only.

Reads reflect the current database snapshot on each call. If a refresh replaces
a message during pagination, restart at zero after the refresh completes.
Reconnect or restart an already-running MCP server to discover the new tool.

CLI equivalent (this command intentionally displays the requested text):

```sh
PYTHONPATH=src .venv/bin/python -m archive_mcp get-message \
  runtime/archive.sqlite PROVIDER ACCOUNT CONVERSATION_ID MESSAGE_ID \
  --offset 4000 --limit 4000
```

For the repeatable search-quality baseline, see [retrieval evaluation](RETRIEVAL_EVALUATION.md).

## Runtime audit log

By default, a server process appends JSONL events to `mcp.jsonl` beside its
database (`runtime/mcp.jsonl` in the standard setup). The server's `--log PATH`
option overrides that location. Events contain only the timestamp, lifecycle
or tool event, tool name, duration, status, safe
error class, and list-result count. Queries, arguments, returned text, account
labels, conversation IDs, and paths are intentionally excluded.

Inspect recent events:

```sh
tail -n 20 runtime/mcp.jsonl
```

```powershell
Get-Content runtime\mcp.jsonl -Tail 20
```

## Conversation kinds

- `conversation`: a provider-supplied ChatGPT, Claude, DeepSeek, or Grok thread.
- `local_session`: a Codex, Claude Code, Antigravity, OpenCode, or Qwen Code session.
- `activity_session`: Gemini activity entries grouped by a deterministic
  60-minute inactivity boundary.

Gemini Takeout does not contain usable conversation IDs, so those sessions are
explicitly marked as inferred.

## Command-line diagnostics

```sh
# Inspect an extracted folder without importing it
PYTHONPATH=src .venv/bin/python -m archive_mcp scan /path/to/export

# Inspect aggregate status
PYTHONPATH=src .venv/bin/python -m archive_mcp status runtime/archive.sqlite

# Review recent import batches and warning counts
PYTHONPATH=src .venv/bin/python -m archive_mcp import-report runtime/archive.sqlite

# Check SQLite, foreign keys, parent links, and FTS indexes
make check
```

Operational read errors return fixed diagnostics and exception types. Search
errors do not echo query text. The audit log records tool names,
outcomes, timings, counts, and exception types, without arguments or content.
The command-line server enables the log by default. Programmatic callers can
omit it with `create_server(database, log=None)`. This describes the archive's
own operational handling, not every SDK validation or client log.

Storage is local; a connected AI client may forward retrieved excerpts to its
model provider. See [privacy and data flow](privacy/README.md).
