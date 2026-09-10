# Development checks

Use synthetic fixtures for automated tests. Keep exports, databases, logs,
source maps, and private evaluations out of Git.

macOS/Linux, after README setup:

~~~sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=src .venv/bin/python -m archive_mcp.evaluate
PYTHONPATH=src .venv/bin/python -m archive_mcp.demo
~~~

Windows PowerShell:

~~~powershell
$env:PYTHONPATH = (Resolve-Path src).Path
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m archive_mcp.evaluate
.\.venv\Scripts\python.exe -m archive_mcp.demo
~~~

With Make, use make test, make demo, and make evaluate. The temporary demo is
also described in [demo](DEMO.md). The demo now verifies a real STDIO server
connection, paginated enumeration, comparison, and original-message retrieval.
CI is configured to run the suite and demo on Ubuntu and Windows with Python
3.10 and 3.13; successful remote runs still need confirmation. The checks do
not read user exports or runtime databases.
Check an imported database using the [user guide](USER_GUIDE.md#check-imports).

On 2026-09-09, all 79 tests, the demo, and the retrieval evaluator passed on
macOS/Python 3.13 from an isolated copy of Git-eligible source files, using a
directory name containing spaces. The copy excluded local configuration,
private archives, environments, and project notes. Existing installed
dependencies were reused: this was source-layout verification, not a fresh
dependency install or a clean clone of the final release commit. The demo
enumerated eight conversations across three pages, searched eight sources, and
resolved original-message evidence from seven sources. Local Markdown file
links also resolved within the source copy.

See [retrieval evaluation](RETRIEVAL_EVALUATION.md) for scoring and limitations,
[MCP tools](MCP_TOOLS.md) for interface behavior, and
[release readiness](OPEN_SOURCE_READINESS.md) for publication checks.
The [documentation audit](DOCUMENTATION_AUDIT.md) records the subsequent full
documentation review and fresh synthetic verification on 2026-09-09.
