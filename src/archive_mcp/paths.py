"""Stable desktop storage outside tool caches and source checkouts."""

import os
from pathlib import Path
import sys


def default_database():
    home = Path.home()
    if sys.platform == "darwin":
        root = home / "Library" / "Application Support" / "AI Pensieve"
    elif sys.platform == "win32":
        root = Path(os.environ.get("LOCALAPPDATA") or home / "AppData" / "Local") / "AI Pensieve"
    else:
        configured = os.environ.get("XDG_DATA_HOME")
        root = Path(configured) if configured and Path(configured).is_absolute() else home / ".local" / "share"
        root /= "ai-pensieve"
    return root / "archive.sqlite"
