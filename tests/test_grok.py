import json
import tempfile
import unittest
from pathlib import Path

from archive_mcp.db import connect, search
from archive_mcp.grok import import_file


FIXTURE = Path(__file__).parents[1] / "fixtures" / "grok.json"


class GrokImportTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.connection = connect(Path(self.temp.name) / "archive.sqlite")

    def tearDown(self):
        self.connection.close()
        self.temp.cleanup()

    def test_import_preserves_branches_and_visible_dialogue_only(self):
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
            "SELECT parent_source_id FROM messages WHERE role = 'assistant' AND text <> ''"
        ).fetchall()
        self.assertEqual([row[0] for row in branches], ["grok-user-1", "grok-user-1"])
        self.assertEqual(search(self.connection, "Grok")[0]["provider"], "grok")
        self.assertEqual(search(self.connection, "hiddenchainmarker"), [])
        self.assertEqual(search(self.connection, "private"), [])

    def test_empty_and_malformed_exports(self):
        empty = Path(self.temp.name) / "empty.json"
        empty.write_text('{"conversations": []}', encoding="utf-8")
        self.assertEqual(import_file(self.connection, empty), {
            "conversations": 0,
            "nodes": 0,
        })

        malformed = Path(self.temp.name) / "malformed.json"
        malformed.write_text("{", encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            import_file(self.connection, malformed)


if __name__ == "__main__":
    unittest.main()
