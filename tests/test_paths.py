import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from archive_mcp.paths import default_database


class DesktopPathsTest(unittest.TestCase):
    def test_platform_defaults_are_independent_of_working_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder) / "home"
            with patch("archive_mcp.paths.Path.home", return_value=home), patch.dict(os.environ, {}, clear=True):
                expected = {
                    "darwin": home / "Library/Application Support/AI Pensieve/archive.sqlite",
                    "win32": home / "AppData/Local/AI Pensieve/archive.sqlite",
                    "linux": home / ".local/share/ai-pensieve/archive.sqlite",
                }
                for platform, path in expected.items():
                    with self.subTest(platform=platform), patch("archive_mcp.paths.sys.platform", platform):
                        self.assertEqual(default_database(), path)
                self.assertFalse(home.exists())

    def test_data_root_overrides_and_relative_xdg_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder) / "home"
            root = Path(folder) / "custom"
            with patch("archive_mcp.paths.Path.home", return_value=home):
                with patch("archive_mcp.paths.sys.platform", "win32"), patch.dict(os.environ, {"LOCALAPPDATA": str(root)}):
                    self.assertEqual(default_database(), root / "AI Pensieve/archive.sqlite")
                with patch("archive_mcp.paths.sys.platform", "linux"):
                    with patch.dict(os.environ, {"XDG_DATA_HOME": str(root)}):
                        self.assertEqual(default_database(), root / "ai-pensieve/archive.sqlite")
                    with patch.dict(os.environ, {"XDG_DATA_HOME": "relative"}):
                        self.assertEqual(default_database(), home / ".local/share/ai-pensieve/archive.sqlite")
