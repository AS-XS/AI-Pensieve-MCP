import json
import sqlite3
from collections import Counter
from contextlib import closing
from pathlib import Path

from .antigravity import import_file as import_antigravity
from .batches import run_batch
from .chatgpt import import_file as import_chatgpt
from .claude import import_file as import_claude
from .claude_code import import_file as import_claude_code
from .claude_context import import_file as import_claude_context
from .codex_local import import_file as import_codex
from .deepseek import import_file as import_deepseek
from .gemini import ACTIVITY_DATE, import_file as import_gemini
from .grok import import_file as import_grok
from .memories import import_file as import_memories
from .opencode import import_file as import_opencode
from .qwen_code import import_file as import_qwen_code
from .zcode import import_file as import_zcode, recognized as recognized_zcode


IMPORTERS = {
    "antigravity": import_antigravity,
    "chatgpt": import_chatgpt,
    "claude": import_claude,
    "claude-context": import_claude_context,
    "claude-code": import_claude_code,
    "codex": import_codex,
    "deepseek": import_deepseek,
    "gemini": import_gemini,
    "grok": import_grok,
    "memories": import_memories,
    "notebooklm": import_gemini,
    "opencode": import_opencode,
    "qwen-code": import_qwen_code,
    "zcode": import_zcode,
}
CANDIDATE_SUFFIXES = {".db", ".html", ".json", ".jsonl", ".sqlite", ".sqlite3"}


def json_format(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None

    if isinstance(data, list) and data and isinstance(data[0], dict):
        first = data[0]
        if "mapping" in first:
            messages = (
                node.get("message") for node in first["mapping"].values()
                if isinstance(node, dict)
            )
            if "inserted_at" in first or any(
                isinstance(message, dict) and "fragments" in message
                for message in messages
            ):
                return "deepseek"
            return "chatgpt"
        if "chat_messages" in first:
            return "claude"
        if "conversations_memory" in first:
            return "claude-context"
    if isinstance(data, dict):
        if (
            {"sessionId", "startTime", "messages"} <= data.keys()
            and isinstance(data["messages"], list)
        ):
            return "qwen-code"
        info = data.get("info")
        if (
            isinstance(info, dict) and "id" in info and "time" in info
            and isinstance(data.get("messages"), list)
        ):
            return "opencode"
        conversations = data.get("conversations")
        if (
            isinstance(conversations, list) and conversations
            and {"conversation", "responses"} <= conversations[0].keys()
        ):
            return "grok"
        if "provider" in data and "memories" in data:
            return "memories"
        if "uuid" in data and "docs" in data and "prompt_template" in data:
            return "claude-context"
        metadata = data.get("metadata")
        if "title" in data and isinstance(metadata, dict) and "createTime" in metadata:
            return "notebooklm"
    return None


def jsonl_format(path):
    try:
        with path.open(encoding="utf-8-sig") as lines:
            for _, line in zip(range(50), lines):
                row = json.loads(line)
                if not isinstance(row, dict):
                    continue
                if row.get("type") == "session_meta" and "payload" in row:
                    return "codex"
                if (
                    row.get("type") == "session_metadata"
                    and row.get("sessionId") and row.get("startTime")
                ):
                    return "qwen-code"
                message = row.get("message")
                if (
                    row.get("sessionId") and row.get("uuid")
                    and "parentUuid" in row and isinstance(message, dict)
                    and isinstance(message.get("parts"), list)
                ):
                    return "qwen-code"
                if (
                    row.get("sessionId") and row.get("uuid")
                    and isinstance(message, dict) and "content" in message
                ):
                    return "claude-code"
    except (UnicodeDecodeError, json.JSONDecodeError):
        pass
    return None


def sqlite_format(path):
    try:
        uri = path.resolve().as_uri() + "?mode=ro&immutable=1"
        with closing(sqlite3.connect(uri, uri=True)) as connection:
            tables = {row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )}
            if recognized_zcode(connection):
                return "zcode"
        if {"trajectory_meta", "trajectory_metadata_blob", "steps"} <= tables:
            return "antigravity"
    except sqlite3.DatabaseError:
        pass
    return None


def detect(path):
    suffix = path.suffix.lower()
    if suffix == ".json":
        return json_format(path)
    if suffix == ".jsonl":
        return jsonl_format(path)
    if suffix == ".html":
        if path.name == "MyActivity.html":
            return "gemini"
        try:
            with path.open(encoding="utf-8-sig") as source:
                text = source.read(1_000_000)
        except UnicodeDecodeError:
            return None
        if "content-cell" in text and ACTIVITY_DATE.search(text):
            return "gemini"
    if suffix in {".db", ".sqlite", ".sqlite3"}:
        return sqlite_format(path)
    return None


def classify(roots):
    found = []
    ignored = []
    seen = set()
    for root in map(Path, roots):
        root.stat()  # A missing selected root is not an empty folder.
        paths = [root] if root.is_file() else root.rglob("*")
        for path in paths:
            if not path.is_file() or path.suffix.lower() not in CANDIDATE_SUFFIXES:
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            kind = detect(path)
            if kind:
                found.append((kind, path))
            else:
                ignored.append(path)
    return (
        sorted(found, key=lambda item: str(item[1])),
        sorted(ignored, key=str),
    )


def discover(roots):
    return classify(roots)[0]


def summary(found):
    return {"files": len(found), "formats": dict(sorted(Counter(
        kind for kind, _ in found
    ).items()))}


def scan_summary(roots):
    found, ignored = classify(roots)
    return {
        "candidate_files": len(found) + len(ignored),
        **summary(found),
        "ignored_files": len(ignored),
    }


def import_all(connection, roots, account="default"):
    found, ignored = classify(roots)
    return run_batch(
        connection,
        ((kind, path, IMPORTERS[kind]) for kind, path in found),
        account,
        "auto",
        len(found) + len(ignored),
        ignored,
    )
