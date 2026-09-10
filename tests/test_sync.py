import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from archive_mcp.db import connect
from archive_mcp.sync import sync_local


class LocalSyncTest(unittest.TestCase):
    def test_only_selected_roots_are_discovered_and_imported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            roots = [root / name for name in ("codex", "claude", "antigravity", "qwen")]
            selected = roots[0] / "session.jsonl"
            roots[0].mkdir()
            selected.touch()
            original_glob = Path.glob

            def selected_glob(path, pattern):
                self.assertEqual(path, roots[0])
                return original_glob(path, pattern)

            with (
                closing(connect(root / "archive.sqlite")) as connection,
                patch.object(Path, "glob", selected_glob),
                patch("archive_mcp.sync.import_codex", return_value={"nodes": 2}) as importer,
            ):
                result = sync_local(connection, *roots, "work", providers=["codex", "codex"])
                self.assertEqual(result["files"], 1)
                self.assertEqual(result["selected_providers"], ["codex"])
                importer.assert_called_once_with(connection, selected, "work")
                empty = sync_local(connection, *roots, providers=[])
                self.assertEqual(empty["files"], 0)
                self.assertEqual(empty["selected_providers"], [])

    def test_invalid_selection_fails_before_discovery(self):
        for providers in (["typo"], "codex", False):
            with self.subTest(providers=providers), patch.object(Path, "glob") as glob:
                with self.assertRaises(ValueError):
                    sync_local(None, *([Path("unused")] * 4), providers=providers)
                glob.assert_not_called()

    def test_sync_discovers_each_native_store(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            codex = root / "codex/2025/01"
            claude = root / "claude/project"
            antigravity = root / "antigravity"
            qwen = root / "qwen/project/chats"
            for folder, name in (
                (codex, "session.jsonl"),
                (claude, "session.jsonl"),
                (antigravity, "conversation.db"),
                (qwen, "session.jsonl"),
            ):
                folder.mkdir(parents=True)
                (folder / name).touch()

            imported = {"conversations": 1, "nodes": 2}
            with closing(connect(root / "archive.sqlite")) as connection:
                with (
                    patch("archive_mcp.sync.import_codex", return_value=imported) as codex_import,
                    patch("archive_mcp.sync.import_claude_code", return_value=imported) as claude_import,
                    patch("archive_mcp.sync.import_antigravity", return_value=imported) as antigravity_import,
                    patch("archive_mcp.sync.import_qwen_code", return_value=imported) as qwen_import,
                ):
                    result = sync_local(
                        connection, root / "codex", root / "claude", antigravity,
                        root / "qwen", "personal",
                    )

            self.assertEqual(result["files"], 4)
            self.assertEqual(result["candidate_files"], 4)
            self.assertEqual(result["conversations"], 4)
            self.assertEqual(result["nodes"], 8)
            self.assertEqual(result["warnings"], {})
            self.assertEqual(result["formats"], {
                "antigravity": 1,
                "claude-code": 1,
                "codex": 1,
                "qwen-code": 1,
            })

            codex_import.assert_called_once()
            claude_import.assert_called_once()
            antigravity_import.assert_called_once()
            qwen_import.assert_called_once()


if __name__ == "__main__":
    unittest.main()
