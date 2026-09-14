import tempfile
import unittest
from pathlib import Path

from import_expectations import expected_result

from archive_mcp.claude_code import import_file
from archive_mcp.db import connect, search


FIXTURE = Path(__file__).parents[1] / "fixtures" / "claude_code.jsonl"


class ClaudeCodeImportTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.connection = connect(Path(self.temp.name) / "archive.sqlite")

    def tearDown(self):
        self.connection.close()
        self.temp.cleanup()

    def test_import_keeps_final_dialogue_only_and_is_idempotent(self):
        self.assertEqual(import_file(self.connection, FIXTURE, "personal"), expected_result({
            "conversations": 1,
            "nodes": 2,
        }))
        import_file(self.connection, FIXTURE, "personal")

        rows = self.connection.execute(
            "SELECT role, text, parent_source_id FROM messages ORDER BY created_at"
        ).fetchall()
        self.assertEqual(len(rows), 2)
        self.assertEqual(tuple(rows[0]), ("user", "How should local sessions be imported?", None))
        self.assertEqual(tuple(rows[1]), (
            "assistant", "Import normalized dialogue into SQLite.", "user-1",
        ))
        self.assertEqual(search(self.connection, "intermediate"), [])
        self.assertEqual(search(self.connection, "notification"), [])
        self.assertEqual(search(self.connection, "private"), [])


if __name__ == "__main__":
    unittest.main()
