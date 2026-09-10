# Contributing

Use synthetic fixtures for tests. Do not commit provider exports, private
databases, logs, source maps, local configuration, or private retrieval labels.

Run the complete local checks before opening a change:

~~~sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=src .venv/bin/python -m archive_mcp.demo
PYTHONPATH=src .venv/bin/python -m archive_mcp.evaluate
~~~

Changes to importers should include a privacy-safe fixture and cover normal,
empty, malformed, duplicate, and provider-specific edge cases. Preserve source
immutability, stable provider/account identities, branch relationships, and
read-only MCP behavior. Do not add network calls, telemetry, hosted services,
routine hashing, or permission prompts without a separate product decision.

For schema changes, update [SCHEMA.md](docs/SCHEMA.md), add a numbered
migration and rollback tests, and explain upgrade behavior. For privacy or
security concerns, follow [SECURITY.md](SECURITY.md); the owner still needs to
configure the private reporting channel before publication. Do not post
sensitive examples in a public issue.
