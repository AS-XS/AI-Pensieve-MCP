# User guide

Run commands from the project folder after completing the README installation.
MCP configuration is in [AI client setup](AI_CLIENTS.md).
Use the [app export guide](EXPORT_GUIDE.md) to obtain the supported files.
Detailed import coverage is in [compatibility](COMPATIBILITY.md).

## Separate accounts

The account label applies to every file in an import command. Keep exports
from different accounts in separate folders and run separate commands.
Changing the label later creates a different source identity.

macOS/Linux:

~~~sh
PYTHONPATH=src .venv/bin/python -m archive_mcp import-auto runtime/archive.sqlite imports/account-one --account account-one
~~~

Windows PowerShell:

~~~powershell
$env:PYTHONPATH = (Resolve-Path src).Path
.\.venv\Scripts\python.exe -m archive_mcp import-auto runtime\archive.sqlite imports\account-one --account account-one
~~~

Repeat for each account folder and label. Extract ZIP files before importing.
The importer detects supported structures inside nested folders.
Missing selected paths now fail with FileNotFoundError; an existing empty folder
still imports successfully with zero candidates. Supported text exports accept
UTF-8 with or without a byte-order mark. Claude Code and Antigravity sessions
with no visible dialogue produce a `no_indexable_records` warning and add no
conversation; previously imported dialogue is preserved.

## Import overlapping exports

For formats with stable original IDs, imports match provider/account, conversation
ID, and message/node ID. Titles and export filenames are not duplicate keys.
Importing a later ChatGPT or Claude export under the same account label updates
existing records and adds new messages to the same thread. Renaming a thread does
not create another copy; different thread IDs sharing a title remain separate.
Appending dialogue to a Codex session and re-importing also retains one session.
These overlap cases are covered by synthetic regression tests.

Keep the account label consistent between imports. Distinct accounts/providers
remain distinct even if their text matches. Current import totals count processed
records, not separate new/changed/unchanged categories.

This is not universal content-based duplicate detection or revision conflict
resolution. Older snapshots imported later can overwrite retained fields, and
some native importers rebuild their derived session snapshots. Gemini activity
uses inferred sessions and replaces the selected account's activity view; Codex
line-based IDs can change after a file rewrite. See [identity mappings](SCHEMA.md)
and [data lifecycle](DATA_LIFECYCLE.md) for format-specific behavior.

## Choose your own source folders

To use a folder in its existing location, no copy into `imports/` is needed.
For example, on macOS/Linux:

~~~sh
PYTHONPATH=src .venv/bin/python -m archive_mcp scan "/path/to/my AI exports"
PYTHONPATH=src .venv/bin/python -m archive_mcp import-auto runtime/archive.sqlite "/path/to/my AI exports" --account personal
~~~

On Windows PowerShell:

~~~powershell
$env:PYTHONPATH = (Resolve-Path src).Path
.\.venv\Scripts\python.exe -m archive_mcp scan "D:\My AI exports"
.\.venv\Scripts\python.exe -m archive_mcp import-auto runtime\archive.sqlite "D:\My AI exports" --account personal
~~~

Both commands accept multiple files or folders. Folder traversal is recursive;
`scan` reports recognized formats without importing. `import-auto` reads the
selected sources in place and writes normalized records into the archive.
It does not move or delete source files. Use the same account label on repeat
imports. Different providers may share a folder, but different accounts should
have separate import commands. You can also save a chosen path in an `exports`
entry in the [refresh configuration](#configure-refreshes).

Path selection is general; parsing remains format-specific. Renaming an
unsupported file or placing it in an official app folder does not make its
contents supported. See the [format evidence and extension policy](COMPATIBILITY.md#importer-evidence-and-custom-locations).

## Check imports

macOS/Linux:

~~~sh
PYTHONPATH=src .venv/bin/python -m archive_mcp import-report runtime/archive.sqlite
PYTHONPATH=src .venv/bin/python -m archive_mcp check runtime/archive.sqlite
~~~

Windows PowerShell:

~~~powershell
$env:PYTHONPATH = (Resolve-Path src).Path
.\.venv\Scripts\python.exe -m archive_mcp import-report runtime\archive.sqlite
.\.venv\Scripts\python.exe -m archive_mcp check runtime\archive.sqlite
~~~

Reports show aggregate counts and warning codes:

- unrecognized_format: no supported structure matched.
- no_indexable_records: the adapter reported zero message nodes and zero memory
  records. Empty-text nodes can prevent this warning; it is not a text audit.
- excluded_review_session: an identified Codex approval-review session was omitted.
- import_failed: a failure occurred; only the exception type is retained.

The check command verifies database and index consistency. It is not a secret
scan or a certification of import completeness.

To enumerate imported conversations without a keyword, use the bounded command:

~~~sh
PYTHONPATH=src .venv/bin/python -m archive_mcp list-conversations runtime/archive.sqlite --limit 50
~~~

Pass the returned `next_cursor` as `--cursor` with the same filters until it is
null. Complete paging while the archive is unchanged. Restart at cursor 0 after
any import, refresh (even a failed attempt), rebuild, or filter/database change.
Paging reads current data; it does not hold a snapshot or detect changes.
Use the MCP `list_conversations` tool for the same operation.

For an evidence-oriented comparison across providers or accounts:

~~~sh
PYTHONPATH=src .venv/bin/python -m archive_mcp cross-reference runtime/archive.sqlite 'project' --candidate-limit 50 --limit 10
~~~

This searches up to 10 sources in provider/account order, retrieving up to 50
candidates **per source** and showing up to five evidence snippets per source.
Each bundle includes dates, stable IDs, and whether more matches may exist.
Sources with no matches are explicit. Check `sources_unexamined`; use
`--provider` and `--account` to search sources skipped by the source limit.
For keyword-free reading of messages and saved context, page through
[`sweep_archive`](ARCHIVE_SWEEP.md). Cross-reference remains bounded keyword
search. A sweep covers its selected scope only after every page is read.

## Broad discovery

For broader discovery, use the source-balanced survey:

~~~sh
PYTHONPATH=src .venv/bin/python -m archive_mcp survey runtime/archive.sqlite --max-chars 12000
~~~

Pass `next_cursor` with `--cursor` to continue. Source statuses show what remains
unread. Before relying on a project's current status, add `--newest-first` to
`get-conversation` and check related conversations for newer updates. See
[survey coverage and budgets](ARCHIVE_SWEEP.md).

## Configure refreshes

Create runtime/sources.json with only the exports you want to refresh:

~~~json
{
  "exports": [
    {"path": "/absolute/path/to/selected-export", "account": "personal"}
  ]
}
~~~

On Windows use a path such as C:/Users/you/Downloads/selected-export.
The example above and the repository's sources.example.json are export-only.
Relative export paths resolve from the terminal's current directory; use
absolute paths if you run refresh from different directories.

macOS/Linux:

~~~sh
PYTHONPATH=src .venv/bin/python -m archive_mcp refresh runtime/archive.sqlite runtime/sources.json
~~~

Windows PowerShell:

~~~powershell
$env:PYTHONPATH = (Resolve-Path src).Path
.\.venv\Scripts\python.exe -m archive_mcp refresh runtime\archive.sqlite runtime\sources.json
~~~

Refresh imports current source snapshots. It does not request new exports from
provider accounts, install a watcher, or guarantee that removing an input file
removes its previously indexed records. See [privacy and removal](privacy/README.md).

## Native coding sessions

Add a local entry with the providers you want to refresh. For example, this
imports only Codex and Claude Code sessions:

~~~json
{
  "exports": [],
  "local": {
    "account": "personal",
    "providers": ["codex", "claude-code"]
  }
}
~~~

| Provider value | Default location | Files selected within that location |
| --- | --- | --- |
| codex | $CODEX_HOME/sessions, or ~/.codex/sessions | All nested .jsonl files |
| claude-code | ~/.claude/projects | .jsonl files one project folder below the root |
| antigravity | ~/.gemini/antigravity/conversations | .db files directly in the root |
| qwen-code | ~/.qwen/projects | .jsonl files under each project's chats folder |

Unselected stores are not scanned. No local entry means no native imports;
an empty providers list selects none. For compatibility, an existing local
entry with no providers field (or null) still selects all four stores. Account
labels identify the imported source; they do not log into provider accounts.

For a one-time import of selected stores:

macOS/Linux:

~~~sh
PYTHONPATH=src .venv/bin/python -m archive_mcp sync-local runtime/archive.sqlite --provider codex --provider claude-code --account personal
~~~

Windows PowerShell:

~~~powershell
$env:PYTHONPATH = (Resolve-Path src).Path
.\.venv\Scripts\python.exe -m archive_mcp sync-local runtime\archive.sqlite --provider codex --provider claude-code --account personal
~~~

Without --provider, sync-local retains its existing all-four behavior. Results
include selected_providers, even when a selected store has no matching files.
Use --codex-root, --claude-root, --antigravity-root, or --qwen-root to override
locations in this command. Use separate commands for different account labels.

To select only particular session files, pass those files to import-auto.
Native-store availability varies by installation; source files stay unchanged.
Selection affects future imports, not records already in the database.

Finish writing sessions before importing them. In particular, close Antigravity
before reading its native database: its adapter uses SQLite immutable mode and
does not provide a consistent view of a database another process is changing.
See the [SQLite immutable-mode contract](https://www.sqlite.org/uri.html).
Claude Code and Antigravity sessions with no retained dialogue are skipped with
a `no_indexable_records` warning. Existing imported dialogue is preserved.
Other import failures still stop the batch; earlier completed files remain imported.

## Make shortcuts

With Make and a POSIX shell (macOS/Linux), these shortcuts use the same commands.
On Windows, use the PowerShell commands above; installing Make alone is insufficient.

| Command | Purpose |
| --- | --- |
| make setup | Create folders/environment and install dependencies |
| make import | Import everything under imports with the default label |
| make import IMPORTS=imports/account-one ACCOUNT=account-one | Import one selected account folder |
| make report | Show recent import reports |
| make refresh | Read runtime/sources.json and import configured sources |
| make check | Check archive integrity |

## Troubleshooting and development

Exceptions during CLI command execution exit with status 1 and print a JSON object containing
the command and exception type to stderr. Raw tracebacks and source details are
omitted. For FileNotFoundError, check the paths you supplied; for JSONDecodeError,
check that the selected file is valid JSON in the expected export format.
Argument-parsing failures instead use argparse's usage output and status 2;
they may echo supplied arguments. A completed `check` can return status 0 with
`"ok": false`, so inspect the JSON result rather than only the exit status.

Confirm the import report before troubleshooting an empty search. Try fewer
keywords and check source/date filters. A result snippet may be truncated;
the client can request exact message pages through MCP.

Tool details, command-line retrieval, and upgrades:
[MCP guide](MCP_TOOLS.md).
Contributor validation: [development guide](DEVELOPMENT.md).
