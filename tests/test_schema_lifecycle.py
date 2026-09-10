import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from archive_mcp.chatgpt import import_file as import_chatgpt
from archive_mcp.db import (
    CONVERSATION_FTS_SCHEMA, SCHEMA_VERSION, connect, initialize,
    integrity_status, search,
)
from archive_mcp.gemini import import_file as import_gemini
from archive_mcp.refresh import refresh_archive


FIXTURES = Path(__file__).parents[1] / "fixtures"


class SchemaLifecycleTest(unittest.TestCase):
    def test_failed_initialization_is_atomic(self):
        with closing(connect(":memory:")) as connection:
            with patch("archive_mcp.db.CONVERSATION_FTS_SCHEMA", CONVERSATION_FTS_SCHEMA + " INVALID SQL;"):
                with self.assertRaises(sqlite3.OperationalError):
                    initialize(connection)
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT count(*) FROM sqlite_master").fetchone()[0], 0)
            initialize(connection)
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], SCHEMA_VERSION)
            self.assertTrue(integrity_status(connection)["ok"])

    def test_legacy_kind_change_rolls_back_with_failed_title_upgrade(self):
        with closing(connect(":memory:")) as connection:
            connection.executescript("""
                CREATE TABLE source_accounts(id INTEGER PRIMARY KEY, provider TEXT, label TEXT);
                CREATE TABLE conversations(
                    id INTEGER PRIMARY KEY, account_id INTEGER, source_id TEXT,
                    source_file TEXT, title TEXT, created_at REAL, updated_at REAL,
                    UNIQUE(account_id, source_id)
                );
                INSERT INTO source_accounts VALUES (1, 'codex', 'example');
                INSERT INTO conversations VALUES (1, 1, 'session', 'synthetic', 'Example', NULL, NULL);
            """)
            before = list(connection.execute("SELECT * FROM conversations"))
            with patch("archive_mcp.db.CONVERSATION_FTS_SCHEMA", CONVERSATION_FTS_SCHEMA + " INVALID SQL;"):
                with self.assertRaises(sqlite3.OperationalError):
                    initialize(connection)
            self.assertEqual(list(connection.execute("SELECT * FROM conversations")), before)
            self.assertNotIn("kind", [r[1] for r in connection.execute("PRAGMA table_info(conversations)")])
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 0)
            initialize(connection)
            self.assertEqual(connection.execute("SELECT kind FROM conversations").fetchone()[0], "local_session")
            self.assertTrue(integrity_status(connection)["ok"])

    def test_current_unversioned_archive_is_adopted_without_reindexing(self):
        with closing(connect(":memory:")) as connection:
            import_chatgpt(connection, FIXTURES / "chatgpt.json", "example")
            connection.execute("PRAGMA user_version = 0")
            before = list(connection.execute("SELECT * FROM messages"))
            changes = connection.total_changes
            initialize(connection)
            self.assertEqual(connection.total_changes, changes)
            self.assertEqual(list(connection.execute("SELECT * FROM messages")), before)
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], SCHEMA_VERSION)
            initialize(connection)
            self.assertEqual(connection.total_changes, changes)
            self.assertTrue(integrity_status(connection)["ok"])

    def test_newer_schema_is_not_modified(self):
        with closing(connect(":memory:")) as connection:
            connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION + 1}")
            with self.assertRaises(ValueError):
                initialize(connection)
            self.assertEqual(connection.execute("SELECT count(*) FROM sqlite_master").fetchone()[0], 0)
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], SCHEMA_VERSION + 1)

    def test_narrower_refresh_retains_old_rows_but_fresh_rebuild_excludes_them(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            config = root / "sources.json"
            config.write_text(json.dumps({"exports": [
                {"path": str(FIXTURES / "chatgpt.json"), "account": "keep"},
                {"path": str(FIXTURES / "chatgpt.json"), "account": "omit"},
            ]}))
            with closing(connect(root / "old.sqlite")) as old:
                refresh_archive(old, config)
                config.write_text(json.dumps({"exports": [
                    {"path": str(FIXTURES / "chatgpt.json"), "account": "keep"},
                ]}))
                refresh_archive(old, config)
                self.assertTrue(search(old, "SQLite", accounts=["omit"]))
                with closing(connect(root / "rebuilt.sqlite")) as rebuilt:
                    refresh_archive(rebuilt, config)
                    refresh_archive(rebuilt, config)
                    self.assertTrue(search(rebuilt, "SQLite", accounts=["keep"]))
                    self.assertEqual(search(rebuilt, "SQLite", accounts=["omit"]), [])
                    self.assertTrue(integrity_status(rebuilt)["ok"])

    def test_missing_chatgpt_records_remain_until_rebuilt(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            revised = root / "revised.json"
            revised.write_text("[]")
            with closing(connect(":memory:")) as connection:
                import_chatgpt(connection, FIXTURES / "chatgpt.json")
                import_chatgpt(connection, revised)
                self.assertTrue(search(connection, "SQLite"))

    def test_gemini_activity_replaces_only_the_selected_account(self):
        with tempfile.TemporaryDirectory() as folder:
            empty = Path(folder) / "empty.html"
            empty.write_text("<html></html>")
            with closing(connect(":memory:")) as connection:
                import_gemini(connection, FIXTURES / "gemini.html", "first")
                import_gemini(connection, FIXTURES / "gemini.html", "second")
                import_gemini(connection, empty, "first")
                self.assertEqual(search(connection, "SQLite", accounts=["first"]), [])
                self.assertTrue(search(connection, "SQLite", accounts=["second"]))
                self.assertTrue(integrity_status(connection)["ok"])
