# Refresh, rebuild, removal, and optional backups

The database is derived from selected local sources. Import and refresh do not
make automatic backups. Users who want a snapshot can choose the optional
procedure below; a backup is not required to use the archive.

## What another import does

| Input or change | Current behavior |
| --- | --- |
| Same records, provider, and account label | Preserves identical content without rewriting it; no duplicate canonical records. Each CLI import batch still adds an operational record. |
| Changed account label | Creates a separate source identity; it does not rename the old account. |
| ChatGPT, Claude, DeepSeek, Grok, Claude Code, Antigravity, OpenCode, Qwen Code, ZCode, or saved context | Upserts imported records subject to the revision rules below. Records absent from a later input generally remain in the existing database. |
| Codex session reimport | Upserts visible nodes and prunes parser-excluded nodes for accepted snapshots; older snapshots cannot replace matching fields or prune a newer tail. Identified approval-review sessions still remove their derived conversation. Other sessions remain. |
| Gemini activity HTML reimport | Replaces that account's derived activity view from one file, updating matching identities and removing omitted sessions/nodes. |
| A path/provider removed from the refresh configuration | Stops future imports from that selection; does not erase already indexed records. |
| A source file deleted outside the archive | No general deletion synchronization. The importer cannot infer whether the missing source was intentionally deleted. |

**Gemini:** use one complete selected activity HTML per account. Multiple
activity files under the same label replace each other's activity; the last
imported file wins. A file that parses to zero activity entries also clears
that account's derived activity. Keep the format limits in the
[export guide](EXPORT_GUIDE.md#gemini-apps) in mind.

Conversation/session imports preserve newer dated metadata and matching message
fields when an older or undated snapshot arrives. Unseen IDs can still restore
missing records. Equal dates, two missing dates, and saved context without mapped
edit dates still accept changed incoming content. Gemini retains its explicit
replacement behavior. See [revision rules](SCHEMA.md#import-revision-policy) and
[change counts](USER_GUIDE.md#read-the-import-counts). Refresh processes
configured export entries in order; detected files within each entry are
processed in sorted path order, followed by selected native stores.

Imports commit per source file. If a later file fails, earlier successful files
can remain imported; the batch report records the failure. A refresh across
multiple exports/stores is not one all-or-nothing transaction. Schema upgrade
rollback is separate from import-batch behavior.

## Rebuild from a smaller selection

To remove a whole source/account from the searchable archive, create a fresh
database using only the files you want. No permission layer or ongoing exclusion
list is involved. There is no built-in per-message deletion command.

1. Create runtime/selected-sources.json with the retained sources. Use explicit
   files or folders that contain only those inputs, and omit native stores you
   do not want. Keep original exports unchanged.
2. Choose an unused database path, for example runtime/selected.sqlite.
   Refreshing an existing database is an incremental import, not a rebuild.
3. Import, inspect status/reports, and check the new database once.
4. Repoint the AI client's MCP database argument to the new absolute path and
   reconnect. Use the same narrowed configuration for later refreshes.

Example configuration, replacing the path with your selected input:

~~~json
{
  "exports": [
    {"path": "/absolute/path/to/retained-export", "account": "personal"}
  ]
}
~~~

macOS/Linux:

~~~sh
PYTHONPATH=src .venv/bin/python -m archive_mcp refresh runtime/selected.sqlite runtime/selected-sources.json
PYTHONPATH=src .venv/bin/python -m archive_mcp status runtime/selected.sqlite
PYTHONPATH=src .venv/bin/python -m archive_mcp import-report runtime/selected.sqlite
PYTHONPATH=src .venv/bin/python -m archive_mcp check runtime/selected.sqlite
~~~

Windows PowerShell:

~~~powershell
$env:PYTHONPATH = (Resolve-Path src).Path
.\.venv\Scripts\python.exe -m archive_mcp refresh runtime\selected.sqlite runtime\selected-sources.json
.\.venv\Scripts\python.exe -m archive_mcp status runtime\selected.sqlite
.\.venv\Scripts\python.exe -m archive_mcp import-report runtime\selected.sqlite
.\.venv\Scripts\python.exe -m archive_mcp check runtime\selected.sqlite
~~~

The old database is not copied or overwritten by this procedure. The new file
is rebuilt from sources. Reimporting an excluded file/native store can restore
its records; opening an old database backup can also expose excluded records.
An archive SQLite backup is not an import-auto source format. There are no
tombstones that override a later explicit import. Removing one message requires a separately
prepared source selection; file-level selection cannot filter individual chats
inside a bulk export.

Synthetic tests verify that excluded accounts stay absent after refreshing a
fresh rebuild with the same narrowed configuration. They also demonstrate that
merely narrowing an existing database's configuration leaves old records there.

## Retire local copies

After switching clients, users can remove the old derived database if they no
longer want it. Stop processes using that database first. Manage its associated
SQLite sidecar files as part of the same retired database, not independently
while a process is running. This project does not automatically delete originals,
old databases, logs, or user-created backups.

Imported attachment exclusions do not remove secrets pasted into retained
messages. Deleting local files does not retract excerpts held by an AI client
or its model provider. Filesystem deletion is not guaranteed secure erasure.
See [privacy boundaries](privacy/README.md).

## Optional backup for users who want one

Choose a destination you control, such as an external drive, and an unused
filename. Backups are full copies of the derived database, including searchable
text and source paths. They do not include original exports, source-selection
configuration files, or standalone logs. Keep those only if you want them too.

If the SQLite command-line tool is installed, open the archive read-only:

~~~sh
sqlite3 -readonly runtime/archive.sqlite
~~~

At its sqlite> prompt, replace the destination below with your chosen path
(use forward slashes on Windows, such as E:/Archive/archive-snapshot.sqlite):

~~~text
.backup '/path/on/your/chosen-drive/archive-snapshot.sqlite'
.quit
~~~

This explicitly creates the snapshot; do not use an existing destination you
want to keep. The SQLite CLI is separate from Python's built-in SQLite library.
The commands are documented in the
[official SQLite shell guide](https://www.sqlite.org/cli.html).

Prefer a database-aware snapshot to copying only the main file from a running
database. For Python integrations, the standard library also provides
[Connection.backup](https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.backup).
Neither option is scheduled or invoked by this archive application.

To use a snapshot later, open it with a compatible archive release, check it,
and point the client to the intended restored database path. It represents the
data at snapshot time; it can contain sources you have since excluded. The
manual backup commands were documentation-reviewed, not run on the project
owner's archive.
