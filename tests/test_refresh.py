import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from import_expectations import expected_result

from archive_mcp.db import connect
from archive_mcp.refresh import refresh_archive


FIXTURES = Path(__file__).parents[1] / "fixtures"


class RefreshTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.connection = connect(self.root / "archive.sqlite")

    def tearDown(self):
        self.connection.close()
        self.temp.cleanup()

    def config(self, data):
        path = self.root / "sources.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_refreshes_exports_idempotently(self):
        config = self.config({"exports": [
            {"path": str(FIXTURES / "chatgpt.json"), "account": "main"},
            {"path": str(FIXTURES / "deepseek.json"), "account": "personal"},
        ]})
        first = refresh_archive(self.connection, config)
        second = refresh_archive(self.connection, config)

        self.assertNotEqual(
            first["exports"].pop("batches"),
            second["exports"].pop("batches"),
        )
        totals = dict(conversations=2, nodes=9)
        self.assertEqual(first["exports"].pop("changes"), expected_result(totals)['changes'])
        self.assertEqual(second["exports"].pop("changes"), expected_result(totals, 'unchanged')['changes'])
        self.assertEqual(first, second)
        self.assertEqual(first["exports"], {
            "candidate_files": 2,
            "files": 2,
            "conversations": 2,
            "nodes": 9,
            "ignored_files": 0,
            "formats": {"chatgpt": 1, "deepseek": 1},
            "warnings": {},
        })
        self.assertEqual(first["archive"]["messages"], 9)

    def test_refreshes_local_stores_when_configured(self):
        config = self.config({"local": {"account": "personal"}})
        roots = (
            Path("codex"), Path("claude"), Path("antigravity"), Path("qwen"),
        )
        with (
            patch("archive_mcp.refresh.default_roots", return_value=roots),
            patch(
                "archive_mcp.refresh.sync_local",
                return_value={"files": 4, "conversations": 4, "nodes": 8},
            ) as sync,
        ):
            result = refresh_archive(self.connection, config)

        sync.assert_called_once_with(self.connection, *roots, "personal", providers=None)
        self.assertEqual(result["local"], {
            "files": 4, "conversations": 4, "nodes": 8,
        })

    def test_export_only_configuration_does_not_discover_native_stores(self):
        with patch("archive_mcp.refresh.default_roots") as roots:
            result = refresh_archive(self.connection, self.config({"exports": []}))
        roots.assert_not_called()
        self.assertEqual(result["local"], {"files": 0})

    def test_refresh_passes_explicit_native_selection(self):
        with patch("archive_mcp.refresh.sync_local", return_value={"files": 0}) as sync:
            refresh_archive(self.connection, self.config({
                "local": {"account": "work", "providers": ["claude-code"]},
            }))
        self.assertEqual(sync.call_args.kwargs, {"providers": ["claude-code"]})
        self.assertEqual(sync.call_args.args[-1], "work")


if __name__ == "__main__":
    unittest.main()
