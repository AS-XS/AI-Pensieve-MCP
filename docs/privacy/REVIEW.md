# Local implementation review

Reviewed 2026-09-05 against the working implementation. This is a bounded code
review with synthetic regression tests, not an independent security audit.

## Intended boundary

One person selects local inputs, imports a derived SQLite archive, and connects
a trusted client through read-only STDIO MCP. That client can read the selected
database. No per-read approvals, account access-control system, or routine
hash verification is needed for this design.

Reviewed source reads, import reporting, SQLite queries and connections, MCP
responses and logging, and CLI failures. Tests use synthetic exports and errors;
the review did not require scanning or hashing private archives.

## Findings and fixes

| Finding | Impact within this local design | Resolution |
| --- | --- | --- |
| Unexpected MCP exceptions reached the SDK with raw exception text, despite the custom audit log recording only error types. | Moderate: source paths or text could enter client-captured process logs. | Convert read errors to fixed messages and exception types before they reach the SDK. |
| Invalid search/date diagnostics included exception text derived from arguments. | Moderate: private query fragments could enter SDK logs. | Return generic search guidance or an exception type without echoing arguments. |
| An unwritable audit-log path could raise an exception containing that path. | Moderate: private directory names could enter SDK logs. | Emit a fixed log-write diagnostic with the error type. |
| CLI execution failures printed raw tracebacks. | Moderate: source paths and source-derived error details could enter terminal captures. | Emit command and exception type as JSON on stderr, with exit status 1. |

These ratings describe accidental disclosure into local logs, not remote
exploits or evidence of uploads. Existing logs are not retroactively cleaned.

## Evidence

- At that review, all 56 synthetic tests passed. New tests exercised unexpected MCP failures,
  invalid FTS/date inputs across all three search tools, an unavailable audit
  path, and real CLI missing/malformed-file failures.
- Synthetic private markers are absent from tested MCP error responses,
  SDK logs, audit records, and CLI failure output.
- Existing tests cover read-only SQLite rejection of writes, removal of the
  structured source_file response field, provider/account identity separation,
  bounded retrieval, repeated imports, and failed-import reporting.
- Source inspection found parameter binding for search and record identities,
  read-only SQLite connections for MCP retrieval, and no application runtime
  network client, shell execution, or hash pass in the import/retrieval code.
  The later synthetic demo intentionally starts a local MCP subprocess.

These are development checks, not checks added to ordinary reads. A dependency
or transport change warrants its own review.

## Accepted limitations and remaining release work

- The connected client may send retrieved text to a cloud model. Read-only
  access prevents archive modification, not copying or forwarding.
- Text can contain secrets and paths. Safe operational errors are not general
  content redaction. Requested search/read output intentionally contains
  evidence; CLI usage errors can echo command arguments.
- Archived instructions remain data. Server guidance cannot guarantee a model
  will resist prompt injection; reflective client behavior needs evaluation.
- Database files and backups have no application encryption or multi-user
  access boundary. Protection rests with the user's machine and filesystem.
- Refresh does not universally synchronize source deletions. Import a smaller
  source selection into a new database; old copies remain separate.
- Large exports can be loaded into memory. This review is not a resource-limit
  benchmark, fuzzing campaign, dependency audit, or platform certification.
- At review time, finer native selection and export instructions were pending.
  They were completed later on 2026-09-05; see the
  [source-selection guide](../USER_GUIDE.md#native-coding-sessions) and
  [export guide](../EXPORT_GUIDE.md). Public-file/history review remains release
  work.

See [privacy and data flow](README.md) and
[release readiness](../OPEN_SOURCE_READINESS.md) for guidance and next work.
