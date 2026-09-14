import os
from pathlib import Path

from .antigravity import import_file as import_antigravity
from .batches import run_batch
from .claude_code import import_file as import_claude_code
from .codex_local import import_file as import_codex
from .qwen_code import import_file as import_qwen_code


LOCAL_PROVIDERS = ("codex", "claude-code", "antigravity", "qwen-code")


def default_roots():
    home = Path.home()
    codex = Path(os.environ.get("CODEX_HOME", home / ".codex")) / "sessions"
    return (
        codex, home / ".claude/projects",
        home / ".gemini/antigravity/conversations", home / ".qwen/projects",
    )


def sync_local(
    connection, codex_root, claude_root, antigravity_root, qwen_root,
    account="default", providers=None,
):
    if providers is None:
        providers = LOCAL_PROVIDERS
    if not isinstance(providers, (list, tuple)) or any(
        provider not in LOCAL_PROVIDERS for provider in providers
    ):
        raise ValueError("local providers must be a list of supported provider names")
    sources = local_sources(codex_root, claude_root, antigravity_root, qwen_root, providers)
    result = run_batch(connection, sources, account, "local")
    result["selected_providers"] = [kind for kind in LOCAL_PROVIDERS if kind in providers]
    return result


def local_sources(codex_root, claude_root, antigravity_root, qwen_root, providers=LOCAL_PROVIDERS):
    """Enumerate supported session files only within known native roots."""
    groups = (
        ("codex", import_codex, codex_root, "**/*.jsonl"),
        ("claude-code", import_claude_code, claude_root, "*/*.jsonl"),
        ("antigravity", import_antigravity, antigravity_root, "*.db"),
        ("qwen-code", import_qwen_code, qwen_root, "*/chats/**/*.jsonl"),
    )
    return [
        (kind, path, importer)
        for kind, importer, root, pattern in groups
        if kind in providers
        for path in sorted(Path(root).glob(pattern))
    ]
