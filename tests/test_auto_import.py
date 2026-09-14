import shutil
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from import_expectations import expected_result

from archive_mcp.auto_import import discover, import_all, scan_summary, summary
from archive_mcp.db import connect, integrity_status


FIXTURES = Path(__file__).parents[1] / "fixtures"


class AutoImportTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "9f86d081884c7d65"
        self.root.mkdir()
        files = {
            "a/chat-data.json": "chatgpt.json",
            "b/history.json": "claude.json",
            "c/activity.html": "gemini.html",
            "d/notebook-data.json": "notebook.json",
            "e/saved-context.json": "memories.json",
            "f/claude-memory.json": "claude_memories.json",
            "g/project-data.json": "claude_project.json",
            "h/session.jsonl": "codex_session.jsonl",
            "i/session.jsonl": "claude_code.jsonl",
            "j/conversations.json": "deepseek.json",
            "k/backend.json": "grok.json",
            "l/session-export.json": "opencode.json",
            "m/session-export.jsonl": "qwen_code.jsonl",
        }
        for target, source in files.items():
            destination = self.root / target
            destination.parent.mkdir()
            shutil.copy(FIXTURES / source, destination)
        (self.root / "unrelated.json").write_text('{"kind": "attachment"}')
        (self.root / "array.json").write_text('[1, 2, 3]')
        (self.root / "null-metadata.json").write_text('{"title": "file", "metadata": null}')

    def tearDown(self):
        self.temp.cleanup()

    def test_hashed_folder_is_detected_and_imported_idempotently(self):
        found = discover([self.root])
        self.assertEqual(summary(found), {
            "files": 13,
            "formats": {
                "chatgpt": 1,
                "claude": 1,
                "claude-code": 1,
                "claude-context": 2,
                "codex": 1,
                "deepseek": 1,
                "gemini": 1,
                "grok": 1,
                "memories": 1,
                "notebooklm": 1,
                "opencode": 1,
                "qwen-code": 1,
            },
        })
        self.assertEqual(scan_summary([self.root]), {
            "candidate_files": 16,
            "files": 13,
            "formats": summary(found)["formats"],
            "ignored_files": 3,
        })

        database = Path(self.temp.name) / "archive.sqlite"
        with closing(connect(database)) as connection:
            first = import_all(connection, [self.root], "personal")
            second = import_all(connection, [self.root], "personal")
            self.assertNotEqual(first["batch_id"], second["batch_id"])
            totals = dict(conversations=10, nodes=33, memories=6)
            self.assertEqual(first['changes'], expected_result(totals)['changes'])
            self.assertEqual(second['changes'], expected_result(totals, 'unchanged')['changes'])
            self.assertEqual(first["candidate_files"], 16)
            self.assertEqual(first["ignored_files"], 3)
            self.assertEqual(first["warnings"], {"unrecognized_format": 3})
            self.assertEqual(first["conversations"], 10)
            self.assertEqual(first["nodes"], 33)
            self.assertEqual(first["memories"], 6)
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM conversations"
            ).fetchone()[0], 10)
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM messages"
            ).fetchone()[0], 33)
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM memories"
            ).fetchone()[0], 6)

    def test_empty_drop_folder_creates_valid_archive(self):
        database = Path(self.temp.name) / "empty.sqlite"
        empty = Path(self.temp.name) / "empty"
        empty.mkdir()

        with closing(connect(database)) as connection:
            result = import_all(connection, [empty])
            batch_id = result.pop("batch_id")
            self.assertEqual(result, {
                "changes": {},
                "candidate_files": 0,
                "files": 0,
                "ignored_files": 0,
                "formats": {},
                "warnings": {},
            })
            self.assertEqual(connection.execute(
                "SELECT status FROM import_batches WHERE id = ?", (batch_id,)
            ).fetchone()[0], "completed")
            self.assertTrue(integrity_status(connection)["ok"])


if __name__ == "__main__":
    unittest.main()
