# Synthetic demo

The demo imports only the generated fixtures committed in `fixtures/` into a
temporary directory, checks the SQLite and FTS indexes, and starts the real MCP
server as a local subprocess. A bundled test client pages conversations,
compares evidence across providers, and retrieves the original messages.
It never reads `imports/`, native stores, the configured runtime database, or
private source exports. Its database and logs are temporary and cleaned up on
normal exit or a handled error; forced termination can leave temporary files.
The demo needs no AI account, model, client registration, or network connection
after the project dependencies are installed.

After setup:

macOS/Linux:

~~~sh
PYTHONPATH=src .venv/bin/python -m archive_mcp.demo
~~~

Windows PowerShell:

~~~powershell
$env:PYTHONPATH = (Resolve-Path src).Path
.\.venv\Scripts\python.exe -m archive_mcp.demo
~~~

With Make:

~~~sh
make demo
~~~

Success exits with code 0 and prints JSON with top-level `ok: true`,
`check.ok: true`, and `mcp.ok: true`. The output includes aggregate counts,
enumeration page counts, and source/message identities for verified evidence.
It omits message text and temporary source paths.

A failed check exits with code 1. Exceptions inside the demo runner return a small
error object on stderr without raw diagnostic paths. Confirm the README
dependency installation, then use the synthetic tests in the
[development guide](DEVELOPMENT.md) to investigate. MCP work is limited to 45
seconds, with a 10-second timeout per read; process cleanup may take additional
time on a failing run. Dependency/import failures before the runner starts are
ordinary Python startup errors and are outside that error handler.

This verifies the local archive and STDIO connection using the bundled client.
It does not verify registration in your chosen AI app or whether its model will
search automatically. Follow the [AI client setup guide](AI_CLIENTS.md) after
importing selected history for that final connection.

The same demo is exercised by `tests/test_demo.py` and runs as part of the full
test suite.
