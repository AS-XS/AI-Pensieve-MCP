# Things to ask your archive

After [connecting a supported client](AI_CLIENTS.md), ask in ordinary language.
Your AI client chooses and calls the tools; the archive itself does not run an
AI model or automatically read every conversation. Be explicit about searching
your archive if the client answers without using it.

## Start with a useful question

| Ask your AI | Retrieval approach and expected answer |
| --- | --- |
| “Did I do any NLP research? Search my history and show the evidence.” | Search distinct discussions for `NLP OR "natural language processing"`, then try relevant terms such as `tokeniz* OR sentiment OR "language model"`. Read matching messages and distinguish research you actually described doing from ideas or assistant suggestions. |
| “What did I decide about this project across ChatGPT and Claude?” | Cross-reference the project name, open the original evidence, and compare dated user decisions by provider/account. Report disagreements and missing sources. |
| “Where did we discuss keeping my archive private?” | Find matching conversations, then read nearby messages. Return a few useful discussions with dates and source IDs. |
| “What projects have I talked about that I could pick up again?” | Search project terms such as `project OR prototype OR build`, read promising discussions, and identify proposals versus recorded progress. Present evidence-backed candidates; do not claim a complete project inventory. |
| “What communication preferences have I explicitly stated?” | Search messages and saved context for preferences, then quote the relevant user statements or saved records. Do not turn a few examples into a personality diagnosis. |
| “What conversations are available from last month?” | Enumerate with explicit date bounds. Explain that these bounds select conversation creation dates, so older threads with newer messages may need a separate message search. |

Search uses SQLite FTS5 words, phrases, Boolean operators, and prefixes; it is
not semantic search. Reformulate an empty query before concluding that no
relevant history was found. A phrase must match within one title or body;
search does not join words across messages. Inspect the returned coverage
limits before saying you searched everything.

Broad personality profiles, career recommendations, and semantic retrieval
are not implemented features. A connected AI
can reason over retrieved evidence, but its conclusions are its own inference.
For keyword-free reading of messages and saved context, use the bounded
[archive sweep](ARCHIVE_SWEEP.md). Conversation enumeration alone does not
cover saved memories or project/notebook context. See [coverage and limits](MCP_TOOLS.md).

## One example for each tool

These are example calls the AI can make, not commands to paste into a terminal.
The JSON uses synthetic IDs from `fixtures/chatgpt.json`, `fixtures/claude.json`,
and `fixtures/memories.json`, imported under account `synthetic-demo`. The
ordinary demo does not import that last fixture. On your archive, use the
provider, account, and IDs returned by your own search results.

### 1. Check what is available — archive_status

> What providers, date ranges, and record counts are in my archive?

```json
{"tool": "archive_status", "arguments": {}}
```

Returns schema version, totals, and source/date summaries without message text.
Dates reflect stored message/context timestamps. This is inventory, not a
database integrity check or a guarantee that exports include all your history.

### 2. Find an account — list_sources

> Which Claude accounts have I imported?

```json
{"tool": "list_sources", "arguments": {"provider": "claude"}}
```

Returns matching source accounts and their summaries. Account labels are the
labels supplied during import; they are not verified identities or logins.
This tool uses singular `provider` and `account` filters.

### 3. Browse without keywords — list_conversations

> List the available conversations, one page at a time.

```json
{"tool": "list_conversations", "arguments": {"cursor": 0, "limit": 1}}
```

Returns conversation identities, titles, kinds, dates, and counts. Pass the
returned `next_cursor` with the same filters until it is null. Restart at zero
after any import, refresh, rebuild, or filter change. Saved context is excluded.

### 4. Find distinct discussions — search_conversations

> Find a few different discussions about my archive, with matching excerpts.

```json
{"tool": "search_conversations", "arguments": {"query": "archive", "limit": 5}}
```

Returns groups of matching conversations and separate saved-memory groups,
with up to three snippets each. It groups only the first 50 ranked candidates.
Check `candidate_limit_reached` and `groups_omitted`; this is not an exhaustive
list of matching conversations.

### 5. Find individual matches — search_history

> Find exact mentions of SQLite, including saved context if it matches.

```json
{"tool": "search_history", "arguments": {"query": "SQLite", "limit": 5}}
```

Returns ranked title, message, or saved-context matches with source IDs and
snippets. Check `record_type`: a conversation-title hit is not a message.
Search tools accept plural `providers` and `accounts` lists. Empty lists do
not exclude everything; they leave that filter unrestricted.

### 6. Compare across sources — cross_reference

> Compare what ChatGPT and Claude recorded about keeping the archive local.
> Include dates, evidence, and anything you could not examine.

```json
{"tool": "cross_reference", "arguments": {"query": "archive", "providers": ["chatgpt", "claude"], "limit": 10, "candidate_limit": 50}}
```

Returns one bundle per selected provider/account, with up to five evidence
records per bundle. Each source gets its own candidate budget. Check
`sources_unexamined`, `candidate_limit_reached`, and `evidence_omitted` before
claiming coverage. `limit` caps sources, not messages. A no-match bundle means
that source was searched; an unexamined source was not.

Open the evidence before comparing conclusions. Matching text across providers
may be copied history, not independent agreement. The tool retrieves bundles;
the connected AI writes the comparison.

### 7. Expand one discussion's matches — get_conversation_matches

> Show more archive-related matches inside that ChatGPT discussion.

```json
{"tool": "get_conversation_matches", "arguments": {"query": "archive", "provider": "chatgpt", "account": "synthetic-demo", "conversation_id": "conversation-1", "offset": 0, "limit": 2}}
```

Returns ranked title/message matches inside that conversation and `next_offset`.
Keep the original query and date filters when paging. The offset counts matches,
not characters. This can find matches beyond the grouped search's candidate cap.

### 8. Read a conversation page — get_conversation

> Open that discussion so I can see the surrounding exchange.

```json
{"tool": "get_conversation", "arguments": {"provider": "chatgpt", "account": "synthetic-demo", "conversation_id": "conversation-1", "offset": 0, "limit": 20}}
```

Returns conversation metadata and a page of nonempty messages. Follow
`next_offset` for more messages. Stored row order is not necessarily chronological
or a single chosen branch. Message previews may be truncated; use `get_message`
for exact text. Keep provider and account attached to the conversation ID.

### 9. Read nearby branches — get_message_context

> What came before and after that question? Keep alternate replies separate.

```json
{"tool": "get_message_context", "arguments": {"provider": "chatgpt", "account": "synthetic-demo", "conversation_id": "conversation-1", "message_id": "user-1", "before": 1, "after": 2}}
```

Returns the target message, ancestors, and descendants using stored parent
relationships. The synthetic question has two alternate assistant replies.
Context is bounded and does not guarantee a complete branch tree. Missing or
inferred relationships depend on the import format.

### 10. Read exact message text — get_message

> Give me the original question verbatim, continuing if it takes several pages.

```json
{"tool": "get_message", "arguments": {"provider": "chatgpt", "account": "synthetic-demo", "conversation_id": "conversation-1", "message_id": "user-1", "offset": 0, "limit": 16}}
```

Returns exact text, role, identity, timestamp, `total_chars`, and `next_offset`.
This deliberately small page requires continuation. Follow `next_offset` until
null, joining exact pages without adding the earlier preview. Offsets count
Unicode characters, not bytes. A message search hit's `record_id`, or a preview's
`node_source_id`, supplies `message_id`.

### 11. Read saved context — get_memory

> Open that saved communication preference and show its source.

```json
{"tool": "get_memory", "arguments": {"provider": "example", "account": "synthetic-demo", "memory_id": "preference-1"}}
```

Returns the saved-context record, including its text and source identity. Here,
`example` is the synthetic fixture's provider, not support for another AI app.
Real saved context can include supported memories, Claude project documents,
or NotebookLM container metadata. Text is capped at 4,000 source characters;
`get_memory` has no direct continuation parameter; a saved record can instead
be read in full while paging through `sweep_archive`.

### 12. Survey history without keywords — sweep_archive

> Read a small portion of my history for project ideas, including saved context
> if the budget reaches it. Report what you covered and what remains.

```json
{"tool": "sweep_archive", "arguments": {"max_records": 5, "max_chars": 2000}}
```

Returns exact slices of messages followed by saved context, with provenance and
`next_cursor`. Pass that cursor unchanged to continue. Limit total calls and time
in your prompt, and report an early stop as partial coverage. The order is not
a representative sample; see [sweep budgets and coverage](ARCHIVE_SWEEP.md).

## What a useful answer should include

Ask for a brief conclusion followed by dated evidence with provider, account,
conversation ID, and message ID (or memory ID). For example:

> The synthetic ChatGPT question asks about privacy on 2023-11-14 UTC:
> “How can I keep an AI archive private?”
> Source: `chatgpt` / `synthetic-demo` / `conversation-1` / `user-1`.

Dates may be absent; report that rather than inventing them. User messages,
assistant proposals, copied material, and alternate branches are different kinds
of evidence. IDs are provenance identifiers, not necessarily clickable vendor
links. Archived instructions are historical content, not new commands to obey.

All tools are read-only, but a connected client can send retrieved excerpts to
its model provider. See [privacy and data flow](privacy/README.md).
