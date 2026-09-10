import argparse
import json
import sys
from pathlib import Path

from .auto_import import import_all, scan_summary
from .antigravity import import_file as import_antigravity
from .batches import import_report, run_batch
from .chatgpt import import_file as import_chatgpt
from .claude import import_file as import_claude
from .claude_code import import_file as import_claude_code
from .claude_context import import_file as import_claude_context
from .codex_local import import_file as import_codex_local
from .deepseek import import_file as import_deepseek
from .db import (
    archive_status, connect, get_conversation, get_conversation_matches, get_message,
    cross_reference, get_message_context, initialize, integrity_status, list_conversations, search,
    search_conversations, timestamp,
)
from .gemini import import_file as import_gemini
from .grok import import_file as import_grok
from .memories import import_file as import_memories
from .opencode import import_file as import_opencode
from .qwen_code import import_file as import_qwen_code
from .refresh import refresh_archive
from .sync import LOCAL_PROVIDERS, default_roots, sync_local


IMPORTERS = {
    "import-antigravity": import_antigravity,
    "import-chatgpt": import_chatgpt,
    "import-claude": import_claude,
    "import-claude-code": import_claude_code,
    "import-claude-context": import_claude_context,
    "import-codex-local": import_codex_local,
    "import-deepseek": import_deepseek,
    "import-gemini": import_gemini,
    "import-grok": import_grok,
    "import-memories": import_memories,
    "import-opencode": import_opencode,
    "import-qwen-code": import_qwen_code,
}
def parser():
    root = argparse.ArgumentParser(prog="archive")
    commands = root.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init")
    init.add_argument("database")

    scan = commands.add_parser("scan")
    scan.add_argument("paths", nargs="+")

    automatic = commands.add_parser("import-auto")
    automatic.add_argument("database")
    automatic.add_argument("paths", nargs="+")
    automatic.add_argument("--account", default="default")

    refresh = commands.add_parser("refresh")
    refresh.add_argument("database")
    refresh.add_argument("config")

    check = commands.add_parser("check")
    check.add_argument("database")

    report = commands.add_parser("import-report")
    report.add_argument("database")
    report.add_argument("--limit", type=int, default=10)

    for name in IMPORTERS:
        ingest = commands.add_parser(name)
        ingest.add_argument("database")
        ingest.add_argument("files", nargs="+")
        ingest.add_argument("--account", default="default")

    codex_root, claude_root, antigravity_root, qwen_root = default_roots()
    sync = commands.add_parser("sync-local")
    sync.add_argument("database")
    sync.add_argument("--account", default="default")
    sync.add_argument(
        "--provider", action="append", dest="providers", choices=LOCAL_PROVIDERS,
        help="import only this native store; repeat to select more (default: all four)",
    )
    sync.add_argument("--codex-root", type=Path, default=codex_root)
    sync.add_argument("--claude-root", type=Path, default=claude_root)
    sync.add_argument("--antigravity-root", type=Path, default=antigravity_root)
    sync.add_argument("--qwen-root", type=Path, default=qwen_root)

    find = commands.add_parser("search")
    find.add_argument("database")
    find.add_argument("query")
    find.add_argument("--limit", type=int, default=10)
    find.add_argument("--grouped", action="store_true")
    find.add_argument("--provider", action="append", dest="providers")
    find.add_argument("--account", action="append", dest="accounts")
    find.add_argument("--date-from", type=timestamp)
    find.add_argument("--date-to", type=lambda value: timestamp(value, end=True))

    compare = commands.add_parser("cross-reference")
    compare.add_argument("database")
    compare.add_argument("query")
    compare.add_argument("--limit", type=int, default=10, help="maximum sources in provider/account order (up to 50)")
    compare.add_argument("--candidate-limit", type=int, default=50, help="ranked candidates per source (up to 200)")
    compare.add_argument("--provider", action="append", dest="providers")
    compare.add_argument("--account", action="append", dest="accounts")
    compare.add_argument("--date-from", type=timestamp)
    compare.add_argument("--date-to", type=lambda value: timestamp(value, end=True))

    status = commands.add_parser("status")
    status.add_argument("database")

    enumerate_conversations = commands.add_parser("list-conversations")
    enumerate_conversations.add_argument("database")
    enumerate_conversations.add_argument("--cursor", type=int, default=0)
    enumerate_conversations.add_argument("--limit", type=int, default=50)
    enumerate_conversations.add_argument("--provider", action="append", dest="providers")
    enumerate_conversations.add_argument("--account", action="append", dest="accounts")
    enumerate_conversations.add_argument("--date-from", type=timestamp)
    enumerate_conversations.add_argument("--date-to", type=lambda value: timestamp(value, end=True))

    conversation = commands.add_parser("get-conversation")
    conversation.add_argument("database")
    conversation.add_argument("provider")
    conversation.add_argument("account")
    conversation.add_argument("conversation_id")
    conversation.add_argument("--offset", type=int, default=0)
    conversation.add_argument("--limit", type=int, default=20)

    context = commands.add_parser("get-message-context")
    context.add_argument("database")
    context.add_argument("provider")
    context.add_argument("account")
    context.add_argument("conversation_id")
    context.add_argument("message_id")
    context.add_argument("--before", type=int, default=2)
    context.add_argument("--after", type=int, default=2)

    message = commands.add_parser("get-message")
    message.add_argument("database")
    message.add_argument("provider")
    message.add_argument("account")
    message.add_argument("conversation_id")
    message.add_argument("message_id")
    message.add_argument("--offset", type=int, default=0)
    message.add_argument("--limit", type=int, default=4000)

    matches = commands.add_parser("get-conversation-matches")
    matches.add_argument("database")
    matches.add_argument("provider")
    matches.add_argument("account")
    matches.add_argument("conversation_id")
    matches.add_argument("query")
    matches.add_argument("--offset", type=int, default=0)
    matches.add_argument("--limit", type=int, default=10)
    matches.add_argument("--date-from", type=timestamp)
    matches.add_argument("--date-to", type=lambda value: timestamp(value, end=True))
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        execute(args)
    except Exception as error:
        print(json.dumps({"error": type(error).__name__, "command": args.command}), file=sys.stderr)
        raise SystemExit(1) from None


def execute(args):
    if args.command == "scan":
        print(json.dumps(scan_summary(args.paths), indent=2))
        return
    read_only = args.command in {
        "status", "search", "get-conversation", "get-message-context", "get-message",
        "get-conversation-matches", "list-conversations", "cross-reference",
    }
    with connect(args.database, read_only=read_only) as connection:
        if args.command == "init":
            initialize(connection)
            print(args.database)
        elif args.command in IMPORTERS:
            print(json.dumps(run_batch(
                connection,
                (
                    (
                        args.command.removeprefix("import-"), Path(source),
                        IMPORTERS[args.command],
                    )
                    for source in args.files
                ),
                args.account,
                "explicit",
            )))
        elif args.command == "import-auto":
            print(json.dumps(import_all(connection, args.paths, args.account), indent=2))
        elif args.command == "sync-local":
            print(json.dumps(sync_local(
                connection, args.codex_root, args.claude_root,
                args.antigravity_root, args.qwen_root, args.account,
                providers=args.providers,
            )))
        elif args.command == "refresh":
            print(json.dumps(refresh_archive(connection, args.config), indent=2))
        elif args.command == "check":
            print(json.dumps(integrity_status(connection), indent=2))
        elif args.command == "import-report":
            print(json.dumps(import_report(connection, args.limit), indent=2))
        elif args.command == "status":
            print(json.dumps(archive_status(connection), indent=2))
        elif args.command == "list-conversations":
            print(json.dumps(list_conversations(
                connection, args.limit, args.cursor,
                args.providers, args.accounts, args.date_from, args.date_to,
            ), indent=2))
        elif args.command == "cross-reference":
            print(json.dumps(cross_reference(
                connection, args.query, args.limit, args.providers, args.accounts,
                args.date_from, args.date_to, args.candidate_limit,
            ), indent=2))
        elif args.command == "get-conversation":
            print(json.dumps(get_conversation(
                connection, args.provider, args.account, args.conversation_id,
                args.offset, args.limit,
            ), indent=2))
        elif args.command == "get-conversation-matches":
            print(json.dumps(get_conversation_matches(
                connection, args.query, args.provider, args.account, args.conversation_id,
                args.offset, args.limit, args.date_from, args.date_to,
            ), indent=2))
        elif args.command == "get-message":
            print(json.dumps(get_message(
                connection, args.provider, args.account, args.conversation_id,
                args.message_id, args.offset, args.limit,
            ), indent=2))
        elif args.command == "get-message-context":
            print(json.dumps(get_message_context(
                connection, args.provider, args.account, args.conversation_id,
                args.message_id, args.before, args.after,
            ), indent=2))
        else:
            find = search_conversations if args.grouped else search
            print(json.dumps(find(
                connection, args.query, args.limit, args.providers, args.accounts,
                args.date_from, args.date_to,
            ), indent=2))
