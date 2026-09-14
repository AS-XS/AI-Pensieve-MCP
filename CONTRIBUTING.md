# Contributing

This project is licensed under [Apache License 2.0](LICENSE).
Contributions are submitted under that license unless explicitly stated otherwise.

Use synthetic fixtures for tests. Do not commit provider exports, private
databases, logs, source maps, local configuration, or private retrieval labels.

Run the complete local checks before opening a change:

~~~sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=src .venv/bin/python -m archive_mcp.demo
PYTHONPATH=src .venv/bin/python -m archive_mcp.evaluate
~~~

CI runs these same three checks on Ubuntu and Windows with Python 3.10 and
3.13. The evaluation uses only temporary synthetic data and makes no model or
network calls. CI also checks its [retrieval baseline](docs/RETRIEVAL_EVALUATION.md):
all cases except the documented synonym miss must pass with full recall.
The synonym case is allowed to improve.

Changes to importers should include a privacy-safe fixture and cover normal,
empty, malformed, duplicate, and provider-specific edge cases. Preserve source
immutability, stable provider/account identities, branch relationships, and
read-only MCP behavior. Do not add network calls, telemetry, hosted services,
routine hashing, or permission prompts without a separate product decision.

For schema changes, update [SCHEMA.md](docs/SCHEMA.md), add a numbered
migration and rollback tests, and explain upgrade behavior. For privacy or
security concerns, use [GitHub Private Vulnerability Reporting](https://github.com/AS-XS/AI-Pensieve-MCP/security/advisories/new)
as described in [SECURITY.md](SECURITY.md). Do not post vulnerability details or
sensitive examples in a public issue.
