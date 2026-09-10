import tempfile
import unittest
from pathlib import Path

from archive_mcp.claude_context import import_file
from archive_mcp.db import connect, search


FIXTURES = Path(__file__).parents[1] / "fixtures"


class ClaudeContextImportTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.connection = connect(Path(self.temp.name) / "archive.sqlite")

    def tearDown(self):
        self.connection.close()
        self.temp.cleanup()

    def test_context_is_searchable_and_idempotent(self):
        sources = [FIXTURES / "claude_memories.json", FIXTURES / "claude_project.json"]
        for source in sources:
            import_file(self.connection, source, "personal")
            import_file(self.connection, source, "personal")

        self.assertEqual(self.connection.execute("SELECT count(*) FROM memories").fetchone()[0], 4)
        result = search(self.connection, "retrieval")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["provider"], "claude")
        self.assertEqual(result[0]["role"], "project_document")


if __name__ == "__main__":
    unittest.main()
