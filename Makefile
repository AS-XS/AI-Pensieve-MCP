.PHONY: setup import report test evaluate demo refresh check mcp

DATABASE ?= runtime/archive.sqlite
SOURCES ?= runtime/sources.json
IMPORTS ?= imports
ACCOUNT ?= default

setup:
	mkdir -p imports runtime
	python3 -m venv .venv
	.venv/bin/python -m pip install -r requirements.txt

import:
	PYTHONPATH=src .venv/bin/python -m archive_mcp import-auto "$(DATABASE)" "$(IMPORTS)" --account "$(ACCOUNT)"

report:
	PYTHONPATH=src .venv/bin/python -m archive_mcp import-report "$(DATABASE)"

test:
	PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v

evaluate:
	PYTHONPATH=src .venv/bin/python -m archive_mcp.evaluate

demo:
	PYTHONPATH=src .venv/bin/python -m archive_mcp.demo

refresh:
	PYTHONPATH=src .venv/bin/python -m archive_mcp refresh "$(DATABASE)" "$(SOURCES)"

check:
	PYTHONPATH=src .venv/bin/python -m archive_mcp check "$(DATABASE)"

mcp:
	PYTHONPATH=src .venv/bin/python -m archive_mcp.mcp_server "$(DATABASE)"
