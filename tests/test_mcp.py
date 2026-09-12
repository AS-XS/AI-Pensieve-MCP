import asyncio
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from mcp import Client

from archive_mcp.chatgpt import import_file as import_chatgpt
from archive_mcp.db import connect
from archive_mcp.mcp_server import create_server
from archive_mcp.memories import import_file as import_memories


FIXTURES = Path(__file__).parents[1] / "fixtures"


class MCPTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "archive.sqlite"
        with closing(connect(self.database)) as connection, connection:
            import_chatgpt(connection, FIXTURES / "chatgpt.json", "personal")
            import_memories(connection, FIXTURES / "memories.json", "personal")

    def tearDown(self):
        self.temp.cleanup()

    def test_error_responses_and_sdk_logs_omit_private_details(self):
        marker = "SYNTHETIC_PRIVATE_DETAIL"
        log = Path(self.temp.name) / "errors.jsonl"

        async def verify():
            async with Client(create_server(self.database, log)) as client:
                with patch("archive_mcp.mcp_server.status", side_effect=ValueError(marker)):
                    result = await client.call_tool("archive_status", {})
                    self.assertTrue(result.is_error)
                    self.assertIn("ValueError", str(result.content))
                    self.assertNotIn(marker, str(result.content))
                for tool in ("search_history", "search_conversations", "get_conversation_matches", "cross_reference"):
                    identity = ({"provider": "chatgpt", "account": "personal",
                                 "conversation_id": "conversation-1"}
                                if tool == "get_conversation_matches" else {})
                    for query in ({"query": marker + ":needle"},
                                  {"query": "archive", "date_from": marker}):
                        result = await client.call_tool(tool, {**identity, **query})
                        self.assertTrue(result.is_error)
                        self.assertNotIn(marker, str(result.content))
                for date in ("date_from", "date_to"):
                    result = await client.call_tool("list_conversations", {date: marker})
                    self.assertTrue(result.is_error)
                    self.assertNotIn(marker, str(result.content))
            missing_log = Path(self.temp.name) / marker / "audit.jsonl"
            async with Client(create_server(self.database, missing_log)) as client:
                result = await client.call_tool("archive_status", {})
                self.assertTrue(result.is_error)
                self.assertNotIn(marker, str(result.content))

        with self.assertLogs(level="INFO") as captured:
            asyncio.run(verify())
        self.assertNotIn(marker, "\n".join(captured.output))
        self.assertNotIn(marker, log.read_text())
        events = [json.loads(line) for line in log.read_text().splitlines()]
        self.assertTrue(all(event["status"] == "error" for event in events))

    def test_read_only_tools(self):
        log = Path(self.temp.name) / "mcp.jsonl"

        async def verify():
            async with Client(create_server(self.database, log)) as client:
                tools = (await client.list_tools()).tools
                self.assertEqual({tool.name for tool in tools}, {
                    "archive_status", "list_sources", "search_history",
                    "get_conversation", "get_message_context", "get_message", "get_memory",
                    "search_conversations", "cross_reference", "get_conversation_matches", "list_conversations", "sweep_archive", "survey_archive",
                })
                self.assertTrue(all(tool.annotations.read_only_hint for tool in tools))
                self.assertTrue(all(tool.annotations.open_world_hint is False for tool in tools))

                status = await client.call_tool("archive_status", {})
                self.assertEqual(status.structured_content["totals"]["messages"], 4)

                found = await client.call_tool("search_history", {"query": "SQLite"})
                result = found.structured_content["result"][0]
                self.assertEqual(result["provider"], "chatgpt")

                enumerated = await client.call_tool("list_conversations", {"limit": 1})
                self.assertFalse(enumerated.is_error)
                self.assertIsNone(enumerated.structured_content["next_cursor"])
                self.assertEqual(enumerated.structured_content["freshness_policy"], "restart_after_import_refresh_or_rebuild")
                compared = await client.call_tool("cross_reference", {"query": "SQLite"})
                self.assertFalse(compared.is_error)
                self.assertEqual(compared.structured_content["bundles"][0]["provider"], "chatgpt")

                page = await client.call_tool("get_conversation", {
                    "provider": "chatgpt",
                    "account": "personal",
                    "conversation_id": "conversation-1",
                    "limit": 2,
                })
                self.assertEqual(len(page.structured_content["messages"]), 2)
                self.assertNotIn("source_file", page.structured_content["conversation"])

                context = await client.call_tool("get_message_context", {
                    "provider": "chatgpt",
                    "account": "personal",
                    "conversation_id": "conversation-1",
                    "message_id": "user-1",
                    "after": 1,
                })
                self.assertEqual(len(context.structured_content["descendants"]), 2)
                self.assertNotIn("source_file", context.structured_content["conversation"])

                saved = await client.call_tool("get_memory", {
                    "provider": "example",
                    "account": "personal",
                    "memory_id": "preference-1",
                })
                self.assertEqual(saved.structured_content["kind"], "custom_instruction")
                self.assertNotIn("source_file", saved.structured_content)

        asyncio.run(verify())

        with closing(connect(self.database, read_only=True)) as connection:
            with self.assertRaises(sqlite3.OperationalError):
                connection.execute("DELETE FROM messages")

        events = [json.loads(line) for line in log.read_text().splitlines()]
        self.assertEqual([event["tool"] for event in events], [
            "archive_status", "search_history", "list_conversations", "cross_reference",
            "get_conversation",
            "get_message_context", "get_memory",
        ])
        self.assertTrue(all(event["status"] == "ok" for event in events))
        serialized = log.read_text()
        self.assertNotIn("SQLite", serialized)
        self.assertNotIn("personal", serialized)
        self.assertNotIn("conversation-1", serialized)

    def test_grouped_search_expands_to_message_context(self):
        log = Path(self.temp.name) / "groups.jsonl"

        async def verify():
            async with Client(create_server(self.database, log)) as client:
                result = await client.call_tool("search_conversations", {"query": "archive", "limit": 5})
                self.assertFalse(result.is_error)
                group = result.structured_content["groups"][0]
                self.assertEqual(group["conversation_id"], "conversation-1")
                self.assertLessEqual(len(group["matches"]), 3)
                args = {k: group[k] for k in ("provider", "account", "conversation_id")}
                first = await client.call_tool("get_conversation_matches", {**args, "query": "archive", "limit": 1})
                self.assertFalse(first.is_error)
                self.assertEqual(first.structured_content["next_offset"], 1)
                second = await client.call_tool("get_conversation_matches", {**args, "query": "archive", "offset": 1})
                matches = first.structured_content["matches"] + second.structured_content["matches"]
                self.assertIsNone(second.structured_content["next_offset"])
                hit = next(r for r in matches if r["record_type"] == "message")
                context = await client.call_tool("get_message_context", {**args, "message_id": hit["record_id"]})
                self.assertFalse(context.is_error)
                self.assertNotIn("source_file", context.structured_content["conversation"])
                saved = await client.call_tool("search_conversations", {"query": '"plain English"'})
                self.assertEqual(saved.structured_content["groups"][0]["group_type"], "memory")
                for tool, args in (
                    ("search_conversations", {"query": "archive", "limit": 51}),
                    ("get_conversation_matches", {**args, "query": "archive", "offset": -1}),
                ):
                    invalid = await client.call_tool(tool, args)
                    self.assertTrue(invalid.is_error)

        asyncio.run(verify())
        for value in ('"query"', "personal", "conversation-1", "plain English"):
            self.assertNotIn(value, log.read_text())

    def test_long_message_continuation_over_mcp(self):
        text = "Private synthetic continuation é🙂. " * 300 + "END"
        with closing(connect(self.database)) as connection, connection:
            connection.execute(
                "UPDATE messages SET text = ? WHERE node_source_id = ?",
                (text, "assistant-local"),
            )
        log = Path(self.temp.name) / "continuation.jsonl"

        async def verify():
            async with Client(create_server(self.database, log)) as client:
                args = {
                    "provider": "chatgpt", "account": "personal",
                    "conversation_id": "conversation-1", "message_id": "assistant-local",
                }
                chunks = []
                offset = 0
                while offset is not None:
                    result = await client.call_tool("get_message", {**args, "offset": offset})
                    self.assertFalse(result.is_error)
                    page = result.structured_content
                    self.assertNotIn("source_file", page)
                    self.assertLessEqual(len(page["text"]), 4000)
                    chunks.append(page["text"])
                    offset = page["next_offset"]
                self.assertEqual("".join(chunks), text)
                for invalid in ({"offset": -1}, {"limit": 0}, {"limit": 4001}):
                    result = await client.call_tool("get_message", {**args, **invalid})
                    self.assertTrue(result.is_error)
                missing = await client.call_tool("get_message", {**args, "account": "missing"})
                self.assertTrue(missing.is_error)

        asyncio.run(verify())
        serialized = log.read_text()
        for private in ("Private synthetic", "personal", "assistant-local", "conversation-1"):
            self.assertNotIn(private, serialized)

    def test_title_search_leads_to_conversation_over_mcp(self):
        with closing(connect(self.database)) as connection, connection:
            connection.execute(
                "UPDATE conversations SET title = 'Orchid field study' WHERE source_id = 'conversation-1'"
            )
        log = Path(self.temp.name) / "titles.jsonl"

        async def verify():
            async with Client(create_server(self.database, log)) as client:
                result = await client.call_tool("search_history", {
                    "query": '"Orchid field"', "providers": ["chatgpt"],
                    "accounts": ["personal"], "date_from": "2023-11-14",
                    "date_to": "2023-11-14", "limit": 1,
                })
                matches = result.structured_content["result"]
                self.assertEqual(len(matches), 1)
                found = matches[0]
                self.assertEqual(found["record_type"], "conversation")
                self.assertEqual(found["matched_field"], "title")
                page = await client.call_tool("get_conversation", {
                    key: found[key] for key in ("provider", "account", "conversation_id")
                })
                self.assertEqual(page.structured_content["conversation"]["title"], "Orchid field study")
                self.assertEqual(page.structured_content["messages"][0]["node_source_id"], "user-1")
                self.assertNotIn("source_file", page.structured_content["conversation"])
                empty = await client.call_tool("search_history", {
                    "query": "Orchid", "accounts": ["missing"],
                })
                self.assertEqual(empty.structured_content["result"], [])

        asyncio.run(verify())
        for private in ("Orchid", "personal", "conversation-1"):
            self.assertNotIn(private, log.read_text())


if __name__ == "__main__":
    unittest.main()
