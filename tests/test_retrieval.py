import tempfile
import unittest
import sqlite3
from pathlib import Path
from unittest.mock import patch

from archive_mcp.chatgpt import import_file as import_chatgpt
from archive_mcp.claude import import_file as import_claude
from archive_mcp.db import (
    archive_status, connect, get_conversation, get_message, get_message_context,
    initialize, integrity_status, search,
)
from archive_mcp.importing import account_id, conversation_id


FIXTURES = Path(__file__).parents[1] / "fixtures"


class RetrievalTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.connection = connect(Path(self.temp.name) / "archive.sqlite")
        import_chatgpt(self.connection, FIXTURES / "chatgpt.json", "personal")
        import_claude(self.connection, FIXTURES / "claude.json", "personal")

    def tearDown(self):
        self.connection.close()
        self.temp.cleanup()

    def test_status_returns_counts_without_content(self):
        status = archive_status(self.connection)

        self.assertEqual(status["schema_version"], 1)
        self.assertEqual(status["totals"], {
            "accounts": 2,
            "conversations": 2,
            "conversation_kinds": {"conversation": 2},
            "messages": 6,
            "memories": 0,
        })
        self.assertEqual({row["provider"] for row in status["sources"]}, {"chatgpt", "claude"})
        self.assertNotIn("text", str(status))

    def test_integrity_status_is_clean_and_content_free(self):
        result = integrity_status(self.connection)

        self.assertTrue(result["ok"])
        self.assertEqual(result["database"], "ok")
        self.assertEqual(result["foreign_key_violations"], 0)
        self.assertEqual(result["unexpected_orphaned_parents"], 0)
        self.assertNotIn("text", str(result))

    def test_search_filters_provider_account_and_date(self):
        self.assertEqual(
            {row["provider"] for row in search(self.connection, '"archive local"')},
            {"chatgpt", "claude"},
        )
        self.assertEqual(
            {row["provider"] for row in search(self.connection, "search*")},
            {"chatgpt", "claude"},
        )
        self.assertEqual(
            {row["provider"] for row in search(self.connection, "archive", providers=["claude"])},
            {"claude"},
        )
        self.assertEqual(search(self.connection, "archive", accounts=["missing"]), [])
        self.assertEqual(
            {row["provider"] for row in search(self.connection, "archive", date_from=1704000000)},
            {"claude"},
        )

    def test_title_search_returns_one_attributed_conversation(self):
        self.connection.execute(
            "UPDATE conversations SET title = 'Orchid field study' WHERE source_id = 'conversation-1'"
        )
        for query in ('Orchid', '"Orchid field"', 'Orch*', 'Orchid AND study', 'text:Orchid'):
            found = search(self.connection, query)
            self.assertEqual(len(found), 1)
            result = found[0]
            self.assertEqual(result["record_type"], "conversation")
            self.assertEqual(result["matched_field"], "title")
            self.assertEqual(result["record_id"], "conversation-1")
            self.assertEqual(result["conversation_kind"], "conversation")
            self.assertIsNone(result["parent_source_id"])
            self.assertIsNone(result["role"])
            page = get_conversation(
                self.connection, result["provider"], result["account"], result["conversation_id"]
            )
            self.assertEqual(page["conversation"]["title"], "Orchid field study")
            self.assertEqual(len(page["messages"]), 3)
        self.assertEqual(search(self.connection, "SQLite")[0]["matched_field"], "text")
        self.assertEqual(search(self.connection, "text:SQLite"), search(self.connection, "SQLite"))

    def test_title_filters_apply_before_limit(self):
        for provider, label, date in (
            ("chatgpt", "work", 100), ("claude", "personal", 200),
            ("chatgpt", "personal", 300),
        ):
            account = account_id(self.connection, provider, label)
            conversation_id(
                self.connection, account, "shared-id", "synthetic",
                "Orchid study", date, 999,
            )
        results = search(
            self.connection, "Orchid", providers=["chatgpt"], accounts=["personal"],
            date_from=300, date_to=300, limit=1,
        )
        self.assertEqual(len(results), 1)
        self.assertEqual((results[0]["provider"], results[0]["account"]), ("chatgpt", "personal"))
        self.assertEqual(results[0]["created_at"], 300)
        self.assertEqual(search(self.connection, "Orchid", date_from=301), [])
        self.assertEqual(search(self.connection, "Orchid", date_to=99), [])
        self.assertEqual(search(self.connection, "Orchid", accounts=["missing"]), [])

    def test_title_index_tracks_rename_reimport_and_delete(self):
        import_chatgpt(self.connection, FIXTURES / "chatgpt.json", "personal")
        import_chatgpt(self.connection, FIXTURES / "chatgpt.json", "personal")
        self.assertEqual(len([
            row for row in search(self.connection, '"Private local archive"')
            if row["record_type"] == "conversation"
        ]), 1)
        with self.connection:
            self.connection.execute(
                "UPDATE conversations SET title = 'Orchid study' WHERE source_id = 'conversation-1'"
            )
        self.assertEqual(search(self.connection, '"Private local archive"'), [])
        self.assertEqual(len(search(self.connection, "Orchid")), 1)
        self.assertEqual(integrity_status(self.connection)["conversation_fts"], "ok")
        with self.connection:
            self.connection.execute("DELETE FROM conversations WHERE source_id = 'conversation-1'")
        self.assertEqual(search(self.connection, "Orchid"), [])
        self.assertEqual(integrity_status(self.connection)["conversation_fts"], "ok")

    def test_conversation_is_paginated(self):
        self.connection.execute(
            "UPDATE messages SET text = ? WHERE node_source_id = ?",
            ("x" * 5000, "assistant-local"),
        )
        first = get_conversation(
            self.connection, "chatgpt", "personal", "conversation-1", limit=2
        )
        second = get_conversation(
            self.connection, "chatgpt", "personal", "conversation-1", offset=2, limit=2
        )

        self.assertEqual([row["node_source_id"] for row in first["messages"]], [
            "user-1", "assistant-local",
        ])
        self.assertEqual(first["next_offset"], 2)
        self.assertTrue(first["messages"][1]["truncated"])
        self.assertEqual(len(first["messages"][1]["text"]), 4001)
        self.assertEqual([row["node_source_id"] for row in second["messages"]], [
            "assistant-cloud",
        ])
        self.assertIsNone(second["next_offset"])

    def test_message_context_preserves_branches(self):
        context = get_message_context(
            self.connection, "chatgpt", "personal", "conversation-1", "user-1",
            before=1, after=1,
        )

        self.assertEqual(context["ancestors"], [])
        self.assertEqual(context["message"]["node_source_id"], "user-1")
        self.assertEqual({row["node_source_id"] for row in context["descendants"]}, {
            "assistant-local", "assistant-cloud",
        })

    def test_long_message_pages_reconstruct_exact_text(self):
        text = "é🙂漢e\u0301\n" * 1800 + "\0Final decision: keep it local."
        self.connection.execute(
            "UPDATE messages SET text = ? WHERE node_source_id = ?",
            (text, "assistant-local"),
        )
        pages = []
        offset = 0
        while offset is not None:
            page = get_message(
                self.connection, "chatgpt", "personal", "conversation-1",
                "assistant-local", offset=offset,
            )
            self.assertEqual(page["offset"], offset)
            self.assertEqual(page["total_chars"], len(text))
            self.assertLessEqual(len(page["text"]), 4000)
            self.assertNotIn("source_file", page)
            pages.append(page["text"])
            offset = page["next_offset"]
        self.assertEqual("".join(pages), text)

    def test_message_page_boundaries_and_identity(self):
        identity = (self.connection, "chatgpt", "personal", "conversation-1")
        self.connection.execute(
            "UPDATE messages SET text = ? WHERE node_source_id = ?",
            ("x" * 8000, "assistant-local"),
        )
        first = get_message(*identity, "assistant-local", limit=9999)
        self.assertEqual(len(first["text"]), 4000)
        self.assertEqual(first["next_offset"], 4000)
        self.assertIsNone(get_message(*identity, "assistant-local", offset=4000)["next_offset"])
        for offset in (8000, 9000):
            page = get_message(*identity, "assistant-local", offset=offset)
            self.assertEqual(page["text"], "")
            self.assertIsNone(page["next_offset"])
        self.assertEqual(get_message(*identity, "root")["text"], "")
        alternate = get_message(*identity, "assistant-cloud", limit=5)
        self.assertEqual(alternate["text"], "The a")
        self.assertEqual(alternate["next_offset"], 5)
        for provider, account, conversation, message in (
            ("claude", "personal", "conversation-1", "assistant-local"),
            ("chatgpt", "missing", "conversation-1", "assistant-local"),
            ("chatgpt", "personal", "missing", "assistant-local"),
            ("chatgpt", "personal", "conversation-1", "missing"),
        ):
            with self.assertRaises(LookupError):
                get_message(self.connection, provider, account, conversation, message)


class MigrationTest(unittest.TestCase):
    def test_existing_titles_are_backfilled_once_and_failed_upgrade_rolls_back(self):
        with tempfile.TemporaryDirectory() as directory:
            connection = connect(Path(directory) / "archive.sqlite")
            import_chatgpt(connection, FIXTURES / "chatgpt.json", "personal")
            connection.executescript("""
                DROP TRIGGER conversations_ai;
                DROP TRIGGER conversations_ad;
                DROP TRIGGER conversations_au;
                DROP TABLE conversation_fts;
                DROP VIEW conversation_search_content;
                PRAGMA user_version = 0;
            """)
            from archive_mcp.db import CONVERSATION_FTS_SCHEMA
            with patch("archive_mcp.db.CONVERSATION_FTS_SCHEMA", CONVERSATION_FTS_SCHEMA + " INVALID SQL;"):
                with self.assertRaises(sqlite3.OperationalError):
                    initialize(connection)
            self.assertIsNone(connection.execute(
                "SELECT 1 FROM sqlite_master WHERE name = 'conversation_fts'"
            ).fetchone())
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 0)
            initialize(connection)
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 1)
            first = search(connection, '"Private local archive"')
            changes = connection.total_changes
            initialize(connection)
            self.assertEqual(connection.total_changes, changes)
            self.assertEqual(search(connection, '"Private local archive"'), first)
            self.assertEqual(len(first), 1)
            self.assertEqual(first[0]["record_type"], "conversation")
            self.assertTrue(integrity_status(connection)["ok"])
            connection.close()

    def test_existing_conversations_receive_kinds(self):
        with tempfile.TemporaryDirectory() as directory:
            connection = connect(Path(directory) / "archive.sqlite")
            with connection:
                connection.executescript("""
                    CREATE TABLE source_accounts (
                        id INTEGER PRIMARY KEY, provider TEXT, label TEXT
                    );
                    CREATE TABLE conversations (
                        id INTEGER PRIMARY KEY, account_id INTEGER, source_id TEXT,
                        source_file TEXT, title TEXT, created_at REAL, updated_at REAL,
                        UNIQUE(account_id, source_id)
                    );
                    INSERT INTO source_accounts VALUES (1, 'chatgpt', 'personal');
                    INSERT INTO source_accounts VALUES (2, 'codex', 'personal');
                    INSERT INTO conversations VALUES (1, 1, 'thread', 'source', '', NULL, NULL);
                    INSERT INTO conversations VALUES (2, 2, 'session', 'source', '', NULL, NULL);
                """)
                initialize(connection)
            kinds = connection.execute(
                "SELECT kind FROM conversations ORDER BY id"
            ).fetchall()
            self.assertEqual([row[0] for row in kinds], ["conversation", "local_session"])
            connection.close()


if __name__ == "__main__":
    unittest.main()
