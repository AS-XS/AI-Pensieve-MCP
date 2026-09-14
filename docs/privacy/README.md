# Privacy and data flow

The archive stores data locally. When an AI client retrieves excerpts, it may
send them to its model provider. Choose the client and its settings accordingly.

## Data flow

~~~text
Selected exports / explicitly enabled native session stores
  -> local importer
  -> local SQLite archive and search indexes
  -> read-only STDIO MCP
  -> connected AI client
  -> possibly a cloud model provider, under the client's settings and policies
~~~

Import and ordinary retrieval require no runtime network requests from this
application. Installing dependencies and updates downloads software.
The optional [desktop prototype](../GUI.md) uses a native webview with bundled
HTML/CSS/JavaScript and a Python bridge directly to the same local import/search
functions. It starts no HTTP server and requests no remote assets or model calls.
Archived text is rendered as text, not executable HTML, and the page blocks
network connections through its content security policy. Its import button can
write the selected local archive; MCP remains read-only. The one-click local import action, or submitting an empty source with the
unmarked bottle, searches the supported apps' known session folders only after
you trigger it. It imports under the displayed account label; it does not scan
the whole computer or download website chats. See [the exact locations](../GUI.md#one-click-local-session-import).
GUI settings are kept
in the current window, not synced to a service. It displays the database path
and source identifiers locally. Future enrichment or remote access needs a
separate data-flow review.

## What is stored

Raw source files remain unchanged. The derived database contains supported
message text, identifiers, roles, dates, source paths, and selected saved context.
See [source-specific coverage](../COMPATIBILITY.md#import-content-and-exclusions).

Metadata exclusions are format-specific. There is no general secret scrubber:
passwords, API keys, health details, and paths pasted into ordinary messages can
remain in the database and retrieved text. Claude project documents can also
contain sensitive text. Excluding attachments does not remove copied content.

MCP responses remove the structured source_file field, not every path that
might appear inside text. The archive's audit log records tool names, timings,
outcomes, and safe counts, without arguments or retrieved content. Client logs,
SDK validation diagnostics, and shell history have their own behavior.

## Access and scope

The current server trusts the local client to read the entire database it opens.
Provider/account/date filters narrow a query; they are not authorization.
A connected client can omit filters or request records directly.

This is the intended trusted single-user design: no per-read permission prompts
or source/account authorization layer. Connect a client to a database whose
contents you want available to it. A separate database containing only selected
sources gives a narrower archive boundary. Routine reads do not hash or verify
source exports.

Read-only MCP prevents archive edits through these tools. It does not stop the
client from retaining, copying, or forwarding retrieved information. Archived
text is untrusted historical data and may contain malicious instructions; server
instructions alone cannot guarantee how every AI client will respond.

## Before importing

1. Keep originals as recovery sources. Extract a working copy and select only
   inputs you want indexed; do not modify original exports.
2. Use an export-only configuration unless you intentionally want native
   sessions included. The [user guide](../USER_GUIDE.md#native-coding-sessions)
   explains exactly which stores the local option discovers.
3. Keep accounts separate at import time. Labels identify sources; they do not
   restrict access.
4. Inspect selected input text for sensitive content you do not want available.
   File-level selection does not redact individual messages inside a file.
5. Review import reports and run the integrity check. Neither detects all
   secrets or proves that every expected record was imported.
6. Connect an AI client only after deciding whether its processing and retention
   behavior is appropriate for this archive.

## Exclusion, deletion, and backups

Deleting or moving a source file does not reliably remove its indexed records.
The current refresh is not a universal synchronization of deletions. See the
[data lifecycle guide](../DATA_LIFECYCLE.md) for provider-specific refresh
behavior and the documented fresh-database rebuild procedure.

To obtain an archive with fewer sources, build a new database from only the
chosen inputs and explicitly repoint the MCP client to it. Review it before
retiring the old database. Old databases, optional backups, indexes, and source
copies must be managed separately; rebuilding does not erase them.

Removing local data cannot retract excerpts already sent to a connected AI
client or its provider. Filesystem deletion is not a promise of secure erasure.

## Local protection and future reflection

The application provides no database encryption or multi-user access boundary.
OS permissions, full-disk encryption, and backup protection matter because
processes with filesystem access may read the data. Git ignore rules reduce
accidental commits but do not prevent forced additions or protect existing Git
history.

Reflection is planned as an on-demand feature with visible scope, evidence,
uncertainty, and no permanent inferred profile by default. It is not an existing
personality-analysis service or a security certification.

See the [implementation review](REVIEW.md) for concrete findings, fixes, and
the limits of the checks performed.
