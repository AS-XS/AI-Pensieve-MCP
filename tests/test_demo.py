import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from archive_mcp.demo import main, run_demo


class DemoTest(unittest.TestCase):
    def test_demo_is_temporary_and_integrity_checked(self):
        result = run_demo()
        self.assertTrue(result["ok"])
        self.assertTrue(result["temporary"])
        self.assertTrue(result["check"]["ok"])
        self.assertGreater(result["status"]["totals"]["conversations"], 0)
        self.assertGreater(result["status"]["totals"]["messages"], 0)
        self.assertTrue(result["example_search"])
        self.assertTrue(result["mcp"]["ok"])
        self.assertEqual(result["mcp"]["transport"], "stdio")
        self.assertGreater(result["mcp"]["enumeration_pages"], 1)
        self.assertEqual(result["mcp"]["conversations_enumerated"], result["status"]["totals"]["conversations"])
        self.assertEqual(result["mcp"]["sources_examined"], len(result["status"]["sources"]))
        self.assertGreaterEqual(len(result["mcp"]["evidence_verified"]), 2)
        self.assertNotIn("text", str(result))

    def test_demo_cli_works_outside_checkout_and_ignores_local_inputs(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            # Deliberately invalid local data would fail if the demo tried to import it.
            (root / "imports").mkdir()
            (root / "runtime").mkdir()
            marker = b"SYNTHETIC_PRIVATE_LOCAL_INPUT"
            inputs = [root / "imports/export.json", root / "runtime/archive.sqlite",
                      root / "runtime/sources.json"]
            for path in inputs:
                path.write_bytes(marker)
            result = subprocess.run(
                [sys.executable, "-m", "archive_mcp.demo"], cwd=root,
                env={**os.environ, "PYTHONPATH": str(Path(__file__).parents[1] / "src")},
                capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)["ok"])
            self.assertNotIn(marker.decode(), result.stdout + result.stderr)
            self.assertNotIn(str(root), result.stdout + result.stderr)
            self.assertEqual(set(root.rglob("*")), {*inputs, root / "imports", root / "runtime"})
            self.assertTrue(all(path.read_bytes() == marker for path in inputs))

    def test_demo_failure_is_nonzero_and_omits_raw_diagnostics(self):
        output, errors = io.StringIO(), io.StringIO()
        with patch("archive_mcp.demo.run_demo", side_effect=RuntimeError("SYNTHETIC_PRIVATE_DETAIL")):
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                self.assertEqual(main(), 1)
        self.assertEqual(output.getvalue(), "")
        self.assertEqual(json.loads(errors.getvalue()), {"ok": False, "error": "RuntimeError"})


if __name__ == "__main__":
    unittest.main()
