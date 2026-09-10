import asyncio
import json
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from mcp import Client
from mcp.client.stdio import StdioServerParameters, stdio_client

from archive_mcp.chatgpt import import_file as import_chatgpt
from archive_mcp.claude import import_file as import_claude
from archive_mcp.db import connect
from archive_mcp.memories import import_file as import_memories


ROOT = Path(__file__).parents[1]


class StdioTest(unittest.TestCase):
    def test_enumerate_compare_and_resolve_original_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "archive.sqlite"
            log = Path(directory) / "audit.jsonl"
            with closing(connect(database)) as connection:
                import_chatgpt(connection, ROOT / "fixtures/chatgpt.json", "personal")
                import_claude(connection, ROOT / "fixtures/claude.json", "personal")
                import_memories(connection, ROOT / "fixtures/memories.json", "personal")
            parameters = StdioServerParameters(
                command=sys.executable,
                args=["-m", "archive_mcp.mcp_server", str(database), "--log", str(log)],
                env={"PYTHONPATH": str(ROOT / "src")}, cwd=ROOT,
            )
            marker = "SYNTHETIC_PRIVATE_DATE"
            with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as stderr:
                async def verify():
                    async with Client(stdio_client(parameters, errlog=stderr), read_timeout_seconds=10) as client:
                        async def call(name, arguments):
                            result = await client.call_tool(name, arguments)
                            self.assertFalse(result.is_error)
                            self.assertNotIn("source_file", str(result.structured_content))
                            return result.structured_content

                        tools = (await client.list_tools()).tools
                        self.assertTrue(all(tool.annotations.read_only_hint for tool in tools))
                        first = await call("list_conversations", {"limit": 1})
                        second = await call("list_conversations", {"limit": 1, "cursor": first["next_cursor"]})
                        self.assertIsNone(second["next_cursor"])
                        identities = {(r["provider"], r["account"], r["conversation_id"])
                                      for r in first["conversations"] + second["conversations"]}
                        self.assertEqual(len(identities), 2)

                        seen_types = set()
                        for query in ("archive", '"plain English"'):
                            compared = await call("cross_reference", {"query": query, "candidate_limit": 3})
                            self.assertEqual(compared["sources_examined"], 3)
                            self.assertEqual(compared["sources_unexamined"], 0)
                            self.assertLessEqual(compared["candidates_examined"], 9)
                            for bundle in compared["bundles"]:
                                for evidence in bundle["evidence"]:
                                    provenance = evidence["provenance"]
                                    source = {k: provenance[k] for k in ("provider", "account")}
                                    kind = evidence["record_type"]
                                    seen_types.add(kind)
                                    if kind == "memory":
                                        original = await call("get_memory", {**source, "memory_id": evidence["record_id"]})
                                        self.assertIn("plain English", original["text"])
                                    else:
                                        identity = {**source, "conversation_id": evidence["conversation_id"]}
                                        self.assertIn(tuple(identity.values()), identities)
                                        if kind == "conversation":
                                            original = await call("get_conversation", identity)
                                            self.assertEqual(original["conversation"]["title"], evidence["title"])
                                        else:
                                            original = await call("get_message", {**identity, "message_id": evidence["record_id"]})
                                            self.assertIn("archive", original["text"].lower())
                                            self.assertEqual(original["role"], evidence["role"])
                        self.assertEqual(seen_types, {"conversation", "message", "memory"})
                        for name in ("list_conversations", "cross_reference"):
                            for date in ("date_from", "date_to"):
                                args = {date: marker}
                                if name == "cross_reference":
                                    args["query"] = "archive"
                                error = await client.call_tool(name, args)
                                self.assertTrue(error.is_error)
                                self.assertNotIn(marker, str(error.content))
                        # A bad request must not prevent subsequent successful reads.
                        status = await call("archive_status", {})
                        self.assertEqual(status["totals"]["messages"], 6)

                asyncio.run(asyncio.wait_for(verify(), timeout=45))
                stderr.seek(0)
                self.assertNotIn(marker, stderr.read())
            events = [json.loads(line) for line in log.read_text().splitlines()]
            self.assertEqual(events[0]["event"], "server_start")
            self.assertTrue(any(e.get("tool") == "get_message" for e in events))
            for private in (marker, "plain English", "personal", "conversation-1"):
                self.assertNotIn(private, log.read_text())
