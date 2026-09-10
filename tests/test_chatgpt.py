import sqlite3
import tempfile
import unittest
from pathlib import Path

from archive_mcp.chatgpt import import_file
from archive_mcp.db import connect, search


FIXTURE = Path(__file__).parents[1] / "fixtures" / "chatgpt.json"


class ChatGPTImportTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.connection = connect(Path(self.temp.name) / "archive.sqlite")

    def tearDown(self):
        self.connection.close()
        self.temp.cleanup()

    def test_import_preserves_branches_and_is_idempotent(self):
        self.assertEqual(import_file(self.connection, FIXTURE, "personal"), {
            "conversations": 1,
            "nodes": 4,
        })
        import_file(self.connection, FIXTURE, "personal")

        self.assertEqual(self.connection.execute("SELECT count(*) FROM conversations").fetchone()[0], 1)
        self.assertEqual(self.connection.execute("SELECT count(*) FROM messages").fetchone()[0], 4)
        parents = self.connection.execute(
            "SELECT parent_source_id FROM messages WHERE node_source_id LIKE 'assistant-%'"
        ).fetchall()
        self.assertEqual([row[0] for row in parents], ["user-1", "user-1"])

    def test_search_returns_provenance(self):
        import_file(self.connection, FIXTURE, "personal")
        result = search(self.connection, "SQLite")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["provider"], "chatgpt")
        self.assertEqual(result[0]["account"], "personal")
        self.assertEqual(result[0]["conversation_id"], "conversation-1")
        self.assertEqual(result[0]["record_id"], "assistant-local")


if __name__ == "__main__":
    unittest.main()
