# Database schema and importer mappings

Schema version **1**, recorded in SQLite's user_version pragma. The executable
definitions are in [db.py](../src/archive_mcp/db.py); common record updates are
in [importing.py](../src/archive_mcp/importing.py). Version 1 names the existing
archive layout and makes its legacy upgrades atomic. It adds no content tables.

## Tables and relationships

| Table | Stored fields | Identity and relationships |
| --- | --- | --- |
| source_accounts | id, provider, label | Unique provider/label pair. Labels are supplied at import, not verified login identities. |
| conversations | id, account_id, source_id, source_file, kind, title, created_at, updated_at | Unique account_id/source_id; account_id references source_accounts. |
| messages | id, conversation_id, node_source_id, message_source_id, parent_source_id, role, text, created_at | Unique conversation_id/node_source_id. Conversation deletion cascades to messages. |
| memories | id, account_id, source_id, source_file, kind, title, text, created_at | Unique account_id/source_id; account_id references source_accounts. Stores selected saved context, projects, documents, and notebook metadata. |
| import_batches | id, mode, account, started_at, completed_at, status, candidate_files, imported_files, warning_count | One operational import attempt, including repeat imports. No per-record batch foreign key. |
| import_warnings | id, batch_id, source_format, code, detail | Batch deletion cascades to warnings. Current failures retain exception type, not raw exception text. |

Each id is an integer primary key. Text fields are required except
message_source_id, parent_source_id, role, and warning source_format.
The message node_source_id is required.
Record dates and batch completed_at can be null. Titles default to empty text;
messages can contain empty text to preserve tree nodes with no visible message.

conversations.kind is conversation, local_session, or activity_session under
current adapters. These are stored text values, not a SQL enum. Projects and
NotebookLM containers live in memories, not separate project/notebook tables.

parent_source_id references the original node identifier inside a conversation;
it is not a database foreign key. Some providers omit parents or point to
excluded records. The integrity command counts unexpected missing parents,
with an exception for the observed Claude export behavior.

There are no attachment, embedding, inferred-profile, permission, backup, or
per-record revision tables. Accounts do not cascade-delete their conversations
or memories. There is no supported SQL deletion interface exposed through MCP.

## Search indexes

| Index | External content | Indexed field |
| --- | --- | --- |
| message_fts | messages, rowid = id | text |
| memory_fts | memories, rowid = id | text |
| conversation_fts | conversation_search_content view over conversations | title, exposed as text |

Insert/update/delete triggers maintain the three FTS5 indexes. The title index
backfills existing titles when it is first installed; it is not rebuilt on
every import or query. The check command explicitly verifies SQLite, foreign
keys, parent references, and FTS consistency. MCP reads do not run that check.

## Identity, dates, and provenance

MCP identifies evidence by provider, account label, original conversation ID,
and node/memory ID. Integer database IDs are local implementation details and
can change when rebuilding. Most source IDs are provider-issued; the derived
identities below have narrower stability guarantees.

source_file records the supplied path for conversations/memories. Reimporting
the same identity from another path updates that field. It is not an immutable
list of every export containing that record. Messages inherit file provenance
through their conversation. The structured source_file field is removed from
MCP responses; paths embedded in text or titles can remain.

Dates are stored as numeric Unix seconds where supplied. Provider-specific
adapters convert ISO timestamps and supported millisecond formats. Missing
optional dates stay null; missing required fields can instead fail the import.
Conversation dates may also be derived from retained messages, as mapped below.
ISO timestamps without a timezone currently use the host's
local timezone during import; timezone-aware inputs are needed for portable
absolute dates. Retrieval date filters without a timezone use UTC.

## Provider field mappings

These describe observed structures, not a vendor commitment to a stable schema.
Fields not mapped here are generally ignored; the importer does not retain raw
JSON blobs or report every unfamiliar field. See
[export limits](EXPORT_GUIDE.md) and [content exclusions](COMPATIBILITY.md#import-content-and-exclusions).

The enumeration cursor uses the local conversation row ID as an opaque traversal
position. It is not a provider identifier and should not be persisted across a
rebuild.

Cross-reference responses are derived from the same FTS records as search. They
do not add comparison tables or merge provider identities; provider and account
remain explicit on every evidence item.

| Adapter | Conversation or saved-context identity | Messages/text and ancestry | Dates |
| --- | --- | --- | --- |
| ChatGPT | id, falling back to conversation_id; title | mapping keys → node IDs; message.id; node.parent; author.role; string content.parts joined with newlines | create_time/update_time; message.create_time |
| Claude | uuid; name → title | chat_messages.uuid; parent_message_uuid; human sender → user; text | conversation created_at/updated_at; message.created_at |
| DeepSeek | id; title | mapping keys; node.parent; REQUEST/RESPONSE fragment content joined; role inferred from fragments | inserted_at/updated_at; message.inserted_at |
| Grok | conversation.id; title | response._id; parent_response_id; human sender → user, others → assistant; message text | conversation create_time/modify_time; response.create_time.$date.$numberLong converted from milliseconds |
| Codex | session_meta.payload.id; working-directory basename in title | response_item message text; node line:N; original item.id where present; preceding retained message as parent; user and final_answer assistant messages only | metadata timestamp and last retained row timestamp; row.timestamp |
| Claude Code | first sessionId; working-directory basename in title | row.uuid; message.id; preceding retained message as parent; selected user content and assistant end_turn text | first/last retained row.timestamp |
| Antigravity | trajectory_meta.cascade_id; decoded workspace basename in title | completed steps (status 3), visible types 14/15; node step:idx; preceding retained step as parent; observed protobuf text fields | observed protobuf seconds/nanoseconds |
| OpenCode | info.id; info.title | message.info.id; parentID when present, otherwise previous retained message; visible text parts | info.time and message.info.time; large numeric values converted from milliseconds |
| Qwen Code | sessionId; working-directory basename where available | uuid; parentUuid followed through omitted nodes to a visible parent; user/assistant text excluding thought parts | startTime and retained row.timestamp |
| Gemini activity | activity-session:START_SECONDS; inferred session title | activity:DATE:user/assistant; sequential parent chain; prompt and exported response | observed English CST dates interpreted as UTC−06:00; gap greater than 60 minutes starts a session |
| NotebookLM | notebook:metadata.createTime → memory source_id | notebook kind; title stored as title and searchable text | metadata.createTime |
| Claude project/context | project:UUID; project-document:PROJECT_UUID:DOC_UUID | project description plus prompt_template; each docs entry's filename/content | project/document created_at |
| Claude memories | conversation-memory; project-memory:PROJECT_ID | conversations_memory and project_memories from the first list entry | unavailable |
| Generic saved context | document.provider plus supplied account; memory.id | memory.kind/title/text | optional memory.created_at |

Codex line IDs can shift if a file is rewritten. Gemini session boundaries can
change with the available activity, and activity at the same timestamp can
collide. NotebookLM identity based on creation time is a fallback, not a vendor
notebook UUID. Antigravity's binary field layout is sample-specific. These
limits should be resolved from representative samples rather than hidden by
hashing or model-generated identity guesses.

Codex review-session exclusion uses an exact prefix on retained user text:
`The following is the Codex agent history`. It is a parser heuristic, not an
authenticated session type; ordinary text beginning with that prefix can also
exclude a session. Codex and Claude Code reconstruct sequential parents rather
than preserving every native branch. ChatGPT retains all string content.parts
regardless of role; string content is not necessarily user-visible dialogue.

## Schema upgrades

| Stored version | Initialization behavior |
| --- | --- |
| 0 | New database or supported legacy archive: create missing baseline objects, add/backfill conversation kind if absent, install/backfill title FTS if absent, then stamp version 1. |
| 1 | Return immediately; no repeated schema creation, migration, or index rebuild. |
| Greater than 1 | Refuse initialization with ValueError; this application does not downgrade future schemas. |

Version 0 supports the known previous layouts, including a fully populated
archive with all current indexes but no version stamp. It is not a repair tool
for arbitrary SQLite files. Provider-format versions are separate and are not
stored as a database schema version.

All version-0 migration DDL, backfills, and the version stamp commit in one
transaction. A failure rolls them back together. Initialization is an import
boundary: call it before starting content writes, not inside a pending content
transaction. Use one importing process at a time.

Run init once after updating the code, as described in
[upgrade commands](MCP_TOOLS.md#upgrading-an-existing-archive). Normal imports
also initialize as needed. Status reports schema_version without migrating;
MCP connections remain read-only. No automatic backup or hash pass runs.

For a future schema change, add an explicit numbered transition and update
SCHEMA_VERSION. Cover supported previous versions, fresh creation, repeated
initialization, preserved evidence, index consistency, and failure rollback.
Do not silently change the meaning of version 1 or assume setting the version
number repairs missing data. Successful upgrades have no automatic downgrade;
reimport retained sources using a compatible release when needed.

Synthetic tests cover fresh/legacy upgrade rollback, kind backfill, title
backfill, adoption without reindexing, repeat initialization, and refusal to
modify a newer schema. They do not create a backup of a user's archive.
