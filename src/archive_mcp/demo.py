"""Run a temporary, privacy-safe archive demo from the bundled fixtures."""

import asyncio
import json
import sys
import tempfile
from contextlib import closing
from pathlib import Path

from mcp import Client
from mcp.client.stdio import StdioServerParameters, stdio_client

from .auto_import import import_all
from .db import archive_status, connect, integrity_status, search


FIXTURES = Path(__file__).parents[2] / "fixtures"
DEMO_FILES = (
    "chatgpt.json", "claude.json", "deepseek.json", "grok.json",
    "gemini.html", "notebook.json", "opencode.json", "qwen_code.jsonl",
)


async def verify_mcp(database, status):
    """Exercise the real server process using only the temporary demo archive."""
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "archive_mcp.mcp_server", str(database),
              "--log", str(database.with_suffix(".jsonl"))],
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[1])},
        cwd=database.parent,
    )
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as stderr:
        async with Client(stdio_client(parameters, errlog=stderr), read_timeout_seconds=10) as client:
            async def call(name, arguments):
                result = await client.call_tool(name, arguments)
                if result.is_error:
                    raise RuntimeError("Synthetic MCP tool call failed.")
                return result.structured_content

            tools = (await client.list_tools()).tools
            if not tools or not all(tool.annotations and tool.annotations.read_only_hint for tool in tools):
                raise RuntimeError("Expected read-only archive tools.")
            identities = set()
            cursor = 0
            pages = 0
            while cursor is not None:
                page = await call("list_conversations", {"limit": 3, "cursor": cursor})
                pages += 1
                for row in page["conversations"]:
                    identity = tuple(row[k] for k in ("provider", "account", "conversation_id"))
                    if identity in identities:
                        raise RuntimeError("Synthetic enumeration repeated a conversation.")
                    identities.add(identity)
                cursor = page["next_cursor"]
            if len(identities) != status["totals"]["conversations"]:
                raise RuntimeError("Synthetic enumeration did not cover the demo archive.")

            compared = await call("cross_reference", {"query": "archive", "candidate_limit": 5})
            if (compared["sources_unexamined"] or
                    compared["sources_examined"] != len(status["sources"])):
                raise RuntimeError("Synthetic comparison did not search every demo source.")
            verified = []
            for bundle in compared["bundles"]:
                hit = next((e for e in bundle["evidence"] if e["record_type"] == "message"), None)
                if hit is None:
                    continue
                source = {k: hit["provenance"][k] for k in ("provider", "account", "conversation_id")}
                original = await call("get_message", {**source, "message_id": hit["record_id"]})
                if (any(original[k] != value for k, value in source.items()) or
                        original["node_source_id"] != hit["record_id"] or
                        original["role"] != hit["role"] or "archive" not in original["text"].lower()):
                    raise RuntimeError("Synthetic evidence did not resolve to its original message.")
                verified.append({**source, "message_id": hit["record_id"]})
            if len(verified) < 2:
                raise RuntimeError("Expected synthetic evidence from multiple sources.")
            return {
                "ok": True, "transport": "stdio", "tool_count": len(tools),
                "enumeration_pages": pages, "conversations_enumerated": len(identities),
                "sources_examined": compared["sources_examined"],
                "evidence_verified": verified,
            }


def run_demo():
    with tempfile.TemporaryDirectory(prefix="personal-ai-archive-demo-") as folder:
        root = Path(folder)
        database = root / "demo.sqlite"
        with closing(connect(database)) as connection:
            result = import_all(
                connection,
                [FIXTURES / name for name in DEMO_FILES],
                "synthetic-demo",
            )
            status = archive_status(connection)
            check = integrity_status(connection)
            hits = search(connection, "archive", 5, None, None, None, None)
        mcp = asyncio.run(asyncio.wait_for(verify_mcp(database, status), timeout=45))
        return {
            "ok": check["ok"] and mcp["ok"],
            "temporary": True,
            "import": {key: value for key, value in result.items() if key != "batch_id"},
            "status": status,
            "check": check,
            "mcp": mcp,
            "example_search": [
                {key: item[key] for key in ("provider", "account", "title", "record_type")}
                for item in hits
            ],
        }


def main():
    try:
        result = run_demo()
    except Exception as error:
        print(json.dumps({"ok": False, "error": type(error).__name__}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
