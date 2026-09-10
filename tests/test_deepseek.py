import json
import tempfile
import unittest
from pathlib import Path

from archive_mcp.db import connect, search
from archive_mcp.deepseek import import_file


FIXTURE = Path(__file__).parents[1] / "fixtures" / "deepseek.json"


class DeepSeekImportTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.connection = connect(Path(self.temp.name) / "archive.sqlite")

    def tearDown(self):
        self.connection.close()
        self.temp.cleanup()

    def test_import_preserves_branches_and_excludes_file_metadata(self):
        self.assertEqual(import_file(self.connection, FIXTURE, "personal"), {
            "conversations": 1,
            "nodes": 5,
        })
        import_file(self.connection, FIXTURE, "personal")

        self.assertEqual(self.connection.execute(
            "SELECT count(*) FROM conversations"
        ).fetchone()[0], 1)
        self.assertEqual(self.connection.execute(
            "SELECT count(*) FROM messages"
        ).fetchone()[0], 5)
        branches = self.connection.execute(
            "SELECT parent_source_id FROM messages WHERE role = 'assistant' ORDER BY node_source_id"
        ).fetchall()
        self.assertEqual([row[0] for row in branches], ["1", "1"])
        file_node = self.connection.execute(
            "SELECT role, text FROM messages WHERE node_source_id = '4'"
        ).fetchone()
        self.assertEqual((file_node["role"], file_node["text"]), ("user", ""))
        self.assertEqual(search(self.connection, "DeepSeek")[0]["provider"], "deepseek")
        self.assertEqual(search(self.connection, "notes"), [])

    def test_empty_and_malformed_exports(self):
        empty = Path(self.temp.name) / "empty.json"
        empty.write_text("[]", encoding="utf-8")
        self.assertEqual(import_file(self.connection, empty), {
            "conversations": 0,
            "nodes": 0,
        })

        malformed = Path(self.temp.name) / "malformed.json"
        malformed.write_text("[", encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            import_file(self.connection, malformed)


if __name__ == "__main__":
    unittest.main()
