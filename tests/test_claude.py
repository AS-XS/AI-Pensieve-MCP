import tempfile
import unittest
from pathlib import Path

from archive_mcp.chatgpt import import_file as import_chatgpt
from archive_mcp.claude import import_file as import_claude
from archive_mcp.db import connect, search


FIXTURES = Path(__file__).parents[1] / "fixtures"


class ClaudeImportTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.connection = connect(Path(self.temp.name) / "archive.sqlite")

    def tearDown(self):
        self.connection.close()
        self.temp.cleanup()

    def test_import_normalizes_roles_and_is_idempotent(self):
        source = FIXTURES / "claude.json"
        self.assertEqual(import_claude(self.connection, source, "personal"), {
            "conversations": 1,
            "nodes": 2,
        })
        import_claude(self.connection, source, "personal")

        messages = self.connection.execute(
            "SELECT node_source_id, parent_source_id, role FROM messages ORDER BY created_at"
        ).fetchall()
        self.assertEqual(len(messages), 2)
        self.assertEqual(tuple(messages[0]), ("claude-user-1", "external-root", "user"))
        self.assertEqual(tuple(messages[1]), ("claude-assistant-1", "claude-user-1", "assistant"))

    def test_search_spans_providers(self):
        import_chatgpt(self.connection, FIXTURES / "chatgpt.json", "personal")
        import_claude(self.connection, FIXTURES / "claude.json", "personal")

        self.assertEqual({row["provider"] for row in search(self.connection, "archive")}, {
            "chatgpt",
            "claude",
        })


if __name__ == "__main__":
    unittest.main()
