import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from import_expectations import expected_result

from archive_mcp.auto_import import import_all, scan_summary
from archive_mcp.batches import run_batch
from archive_mcp.claude_code import import_file as import_claude_code
from archive_mcp.antigravity import import_file as import_antigravity
from archive_mcp.db import connect, integrity_status
from test_antigravity import create_source


FIXTURES = Path(__file__).parents[1] / "fixtures"


class ImportReliabilityTest(unittest.TestCase):
    def test_bom_detection_and_import_agree_for_every_text_fixture(self):
        names = ["chatgpt.json", "claude.json", "claude_code.jsonl",
                 "claude_memories.json", "claude_project.json", "codex_session.jsonl",
                 "deepseek.json", "gemini.html", "grok.json", "memories.json",
                 "notebook.json", "opencode.json", "qwen_code.jsonl"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            expected = None
            for encoding in ("utf-8", "utf-8-sig"):
                inputs = root / encoding
                inputs.mkdir()
                originals = {}
                for name in names:
                    target = inputs / name
                    target.write_text((FIXTURES / name).read_text(), encoding=encoding)
                    originals[target] = target.read_bytes()
                with closing(connect(root / f"{encoding}.sqlite")) as db:
                    result = import_all(db, [inputs])
                    again = import_all(db, [inputs])
                    result.pop("batch_id")
                    again.pop("batch_id")
                    totals = dict(conversations=10, nodes=33, memories=6)
                    self.assertEqual(result.pop("changes"), expected_result(totals)['changes'])
                    self.assertEqual(again.pop("changes"), expected_result(totals, 'unchanged')['changes'])
                    self.assertEqual(result, again)
                    self.assertEqual(result["files"], len(names))
                    if expected is None:
                        expected = result
                    self.assertEqual(result, expected)
                    self.assertTrue(integrity_status(db)["ok"])
                for path, original in originals.items():
                    self.assertEqual(path.read_bytes(), original)

    def test_missing_selected_path_fails_before_importing_other_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(FileNotFoundError):
                scan_summary([root / "missing"])
            with closing(connect(root / "archive.sqlite")) as db:
                with self.assertRaises(FileNotFoundError):
                    import_all(db, [FIXTURES / "chatgpt.json", root / "missing"])
                self.assertEqual(db.execute("SELECT count(*) FROM sqlite_master").fetchone()[0], 0)

    def test_empty_native_sessions_warn_and_preserve_existing_dialogue(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            claude = root / "session.jsonl"
            claude.write_bytes((FIXTURES / "claude_code.jsonl").read_bytes())
            antigravity = root / "conversation.db"
            create_source(antigravity)
            with closing(connect(root / "archive.sqlite")) as db:
                import_claude_code(db, claude)
                import_antigravity(db, antigravity)
                original = [tuple(r) for r in db.execute("SELECT * FROM messages")]
                claude.write_text(json.dumps({"type": "user", "sessionId": "empty",
                                             "uuid": "empty", "message": {"content": []}}))
                with closing(sqlite3.connect(antigravity)) as native, native:
                    native.execute("DELETE FROM steps WHERE step_type IN (14, 15)")
                    native.execute("DELETE FROM trajectory_meta")
                    native.execute("DELETE FROM trajectory_metadata_blob")
                result = run_batch(db, [("claude-code", claude, import_claude_code),
                                        ("antigravity", antigravity, import_antigravity)],
                                   "default", "explicit")
                self.assertEqual(result["warnings"], {"no_indexable_records": 2})
                self.assertEqual(result["conversations"], 0)
                self.assertEqual(result["nodes"], 0)
                self.assertEqual([tuple(r) for r in db.execute("SELECT * FROM messages")], original)
                self.assertEqual(db.execute("SELECT count(*) FROM conversations").fetchone()[0], 2)
                self.assertTrue(integrity_status(db)["ok"])
