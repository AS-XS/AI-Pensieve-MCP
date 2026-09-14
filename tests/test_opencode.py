import json
import tempfile
import unittest
from pathlib import Path

from import_expectations import expected_result

from archive_mcp.db import connect, search
from archive_mcp.opencode import import_file


FIXTURE = Path(__file__).parents[1] / "fixtures" / "opencode.json"


class OpenCodeImportTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.connection = connect(Path(self.temp.name) / "archive.sqlite")

    def tearDown(self):
        self.connection.close()
        self.temp.cleanup()

    def test_imports_visible_dialogue_only_and_is_idempotent(self):
        expected = {"conversations": 1, "nodes": 2}
        self.assertEqual(import_file(self.connection, FIXTURE, "personal"), expected_result(expected))
        self.assertEqual(import_file(self.connection, FIXTURE, "personal"), expected_result(expected, state='unchanged'))

        rows = self.connection.execute(
            "SELECT role, parent_source_id FROM messages ORDER BY created_at"
        ).fetchall()
        self.assertEqual([tuple(row) for row in rows], [
            ("user", None),
            ("assistant", "msg_user_1"),
        ])
        self.assertEqual(search(self.connection, "archive")[0]["provider"], "opencode")
        self.assertEqual(search(self.connection, "hiddenreasoningmarker"), [])
        self.assertEqual(search(self.connection, "hiddentoolmarker"), [])
        self.assertEqual(search(self.connection, "privatefilemarker"), [])

    def test_empty_and_malformed_exports(self):
        empty = Path(self.temp.name) / "empty.json"
        empty.write_text(json.dumps({
            "info": {
                "id": "ses_empty",
                "title": "Empty session",
                "time": {"created": 1756684800000, "updated": 1756684800000},
            },
            "messages": [],
        }), encoding="utf-8-sig")
        self.assertEqual(import_file(self.connection, empty), expected_result({
            "conversations": 1,
            "nodes": 0,
        }))

        malformed = Path(self.temp.name) / "malformed.json"
        malformed.write_text("{", encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            import_file(self.connection, malformed)


if __name__ == "__main__":
    unittest.main()
