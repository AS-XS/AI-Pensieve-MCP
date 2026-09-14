import tempfile
import unittest
from pathlib import Path

from import_expectations import expected_result

from archive_mcp.db import connect, search
from archive_mcp.gemini import import_file


FIXTURES = Path(__file__).parents[1] / "fixtures"


class GeminiImportTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.connection = connect(Path(self.temp.name) / "archive.sqlite")

    def tearDown(self):
        self.connection.close()
        self.temp.cleanup()

    def test_activity_excludes_file_metadata_and_is_idempotent(self):
        source = FIXTURES / "gemini.html"
        self.assertEqual(import_file(self.connection, source, "personal"), expected_result({
            "conversations": 2,
            "nodes": 5,
        }))
        import_file(self.connection, source, "personal")

        messages = self.connection.execute(
            "SELECT role, text FROM messages ORDER BY created_at, role DESC"
        ).fetchall()
        self.assertEqual(len(messages), 5)
        self.assertNotIn("example-notes.pdf", " ".join(row["text"] for row in messages))
        self.assertEqual(
            [row["role"] for row in messages],
            ["user", "assistant", "user", "assistant", "user"],
        )
        sessions = self.connection.execute(
            """
            SELECT c.kind, count(m.id) AS messages
            FROM conversations c JOIN messages m ON m.conversation_id = c.id
            GROUP BY c.id ORDER BY c.created_at
            """
        ).fetchall()
        self.assertEqual([tuple(row) for row in sessions], [
            ("activity_session", 4), ("activity_session", 1),
        ])
        self.assertEqual(
            search(self.connection, "SQLite")[0]["conversation_kind"],
            "activity_session",
        )

    def test_notebook_container_is_searchable_and_idempotent(self):
        source = FIXTURES / "notebook.json"
        self.assertEqual(import_file(self.connection, source, "personal"), expected_result({"memories": 1}))
        import_file(self.connection, source, "personal")

        result = search(self.connection, "research")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["provider"], "notebooklm")
        self.assertEqual(result[0]["role"], "notebook")


if __name__ == "__main__":
    unittest.main()
