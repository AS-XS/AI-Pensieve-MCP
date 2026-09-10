import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CLIErrorTest(unittest.TestCase):
    def test_import_failures_do_not_print_source_paths_or_tracebacks(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "SYNTHETIC_PRIVATE_EXPORT.json"
            database = Path(folder) / "archive.sqlite"
            for expected in ("FileNotFoundError", "JSONDecodeError"):
                with self.subTest(error=expected):
                    result = subprocess.run(
                        [sys.executable, "-m", "archive_mcp", "import-chatgpt",
                         str(database), str(source)], capture_output=True, text=True,
                    )
                    self.assertEqual(result.returncode, 1)
                    self.assertEqual(result.stdout, "")
                    self.assertEqual(json.loads(result.stderr), {
                        "error": expected, "command": "import-chatgpt",
                    })
                    self.assertNotIn("SYNTHETIC_PRIVATE_EXPORT", result.stderr)
                    self.assertNotIn("Traceback", result.stderr)
                    source.write_text("SYNTHETIC_PRIVATE_CONTENT", encoding="utf-8")
