import asyncio
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from mcp import Client
from mcp.client.stdio import StdioServerParameters, stdio_client

from archive_mcp.db import connect, initialize
from archive_mcp.importing import account_id, conversation_id, upsert_message, upsert_memory
from archive_mcp.sweep import sweep_archive


ROOT = Path(__file__).parents[1]


class SweepTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "archive.sqlite"
        self.expected = {}
        with closing(connect(self.database)) as db:
            initialize(db)
            with db:
                for provider, account in [("chatgpt", "one"), ("claude", "two")]:
                    aid = account_id(db, provider, account)
                    cid = conversation_id(db, aid, "shared-id", "SYNTHETIC_PRIVATE_PATH",
                                          "Synthetic project", 100, 200)
                    upsert_message(db, cid, "root", None, None, None, "", None)
                    for mid, text, role in [("user", "🙂研究\x00é" * 30, "user"),
                                            ("answer", "A duplicated assistant suggestion", "assistant")]:
                        upsert_message(db, cid, mid, None, "root", role, text, 100)
                        self.expected[("message", provider, account, "shared-id", mid)] = text
                    text = "A saved project document. " * 400
                    upsert_memory(db, aid, "saved", "SYNTHETIC_PRIVATE_PATH", "project_document",
                                  "Saved context", text, 200)
                    self.expected[("memory", provider, account, None, "saved")] = text
                upsert_memory(db, aid, "empty", "SYNTHETIC_PRIVATE_PATH", "memory", "Empty", "")
                self.expected[("memory", "claude", "two", None, "empty")] = ""

    def tearDown(self):
        self.temp.cleanup()

    def test_complete_traversal_preserves_exact_unicode_text_and_source_identity(self):
        actual, seen = {}, set()
        cursor = None
        with closing(connect(self.database, read_only=True)) as db:
            for _ in range(400):
                page = sweep_archive(db, cursor, max_records=2, max_chars=137)
                self.assertLessEqual(len(page["records"]), 2)
                self.assertLessEqual(page["characters_returned"], 137)
                self.assertNotIn("SYNTHETIC_PRIVATE_PATH", json.dumps(page))
                for record in page["records"]:
                    key = tuple(record[k] for k in ["record_type", "provider", "account",
                                                    "conversation_id", "record_id"])
                    identity = (*key, record["offset"])
                    self.assertNotIn(identity, seen)
                    seen.add(identity)
                    self.assertEqual(record["offset"], len(actual.get(key, "")))
                    actual[key] = actual.get(key, "") + record["text"]
                cursor = page["next_cursor"]
                if cursor is None:
                    self.assertTrue(page["remaining_scope_exhausted"])
                    break
            else:
                self.fail("Sweep did not terminate")
            self.assertEqual(actual, self.expected)
            self.assertEqual(db.execute("SELECT count(*) FROM messages").fetchone()[0], 6)

    def test_source_and_record_date_filters_and_saved_context_continuation(self):
        with closing(connect(self.database, read_only=True)) as db:
            page = sweep_archive(db, providers=["claude"], accounts=["two"],
                                 date_from=200, max_chars=4000)
            self.assertEqual(len(page["records"]), 1)
            self.assertEqual(page["records"][0]["record_type"], "memory")
            self.assertFalse(page["records"][0]["record_complete"])
            cursor = page["next_cursor"]
            with self.assertRaises(ValueError):
                sweep_archive(db, cursor, providers=["chatgpt"], accounts=["two"], date_from=200)
            next_page = sweep_archive(db, cursor, providers=["claude"], accounts=["two"],
                                      date_from=200, max_chars=16000)
            self.assertEqual(next_page["records"][0]["offset"], 4000)
            self.assertIsNone(next_page["next_cursor"])
            self.assertEqual(sweep_archive(db, providers=["absent"])["records"], [])

    def test_bad_cursors_and_timeout_do_not_break_followup_reads(self):
        with closing(connect(self.database, read_only=True)) as db:
            for cursor in ["secret marker", "[]", "null", '[1,0,-1,0,[[],[],null,null]]']:
                with self.assertRaises(ValueError):
                    sweep_archive(db, cursor)
            with patch("archive_mcp.sweep.time.monotonic", side_effect=[0, 3]):
                with self.assertRaises(TimeoutError):
                    sweep_archive(db)
            self.assertTrue(sweep_archive(db)["records"])
            with self.assertRaises(ValueError):
                sweep_archive(db, max_chars=0)

    def test_stdio_reads_and_cursor_errors_are_private(self):
        log = Path(self.temp.name) / "audit.jsonl"
        parameters = StdioServerParameters(command=sys.executable,
            args=["-m", "archive_mcp.mcp_server", str(self.database), "--log", str(log)],
            env={"PYTHONPATH": str(ROOT / "src")})

        async def verify():
            async with Client(stdio_client(parameters), read_timeout_seconds=10) as client:
                tools = (await client.list_tools()).tools
                tool = next(t for t in tools if t.name == "sweep_archive")
                self.assertTrue(tool.annotations.read_only_hint)
                result = await client.call_tool("sweep_archive", {"max_chars": 5})
                self.assertFalse(result.is_error)
                cursor = result.structured_content["next_cursor"]
                result = await client.call_tool("sweep_archive", {"cursor": cursor, "max_chars": 5})
                self.assertFalse(result.is_error)
                self.assertEqual(result.structured_content["records"][0]["offset"], 5)
                for args in [{"cursor": "SYNTHETIC_PRIVATE_CURSOR"},
                             {"date_from": "SYNTHETIC_PRIVATE_DATE"}]:
                    result = await client.call_tool("sweep_archive", args)
                    self.assertTrue(result.is_error)
                    self.assertNotIn("SYNTHETIC_PRIVATE", str(result.content))
        asyncio.run(verify())
        self.assertNotIn("SYNTHETIC_PRIVATE", log.read_text())

    def test_cli_sweep_uses_the_read_only_database(self):
        result = subprocess.run([sys.executable, "-m", "archive_mcp", "sweep",
                                 str(self.database), "--max-chars", "5"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["characters_returned"], 5)
