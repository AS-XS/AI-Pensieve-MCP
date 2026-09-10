import tempfile
import unittest
from pathlib import Path

from archive_mcp.db import connect, search
from archive_mcp.memories import import_file


FIXTURE = Path(__file__).parents[1] / "fixtures" / "memories.json"


class MemoryImportTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.connection = connect(Path(self.temp.name) / "archive.sqlite")

    def tearDown(self):
        self.connection.close()
        self.temp.cleanup()

    def test_memory_is_searchable_and_idempotent(self):
        self.assertEqual(import_file(self.connection, FIXTURE, "personal"), {"memories": 1})
        import_file(self.connection, FIXTURE, "personal")

        result = search(self.connection, "calm")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["record_type"], "memory")
        self.assertEqual(result[0]["record_id"], "preference-1")
        self.assertEqual(result[0]["provider"], "example")


if __name__ == "__main__":
    unittest.main()
