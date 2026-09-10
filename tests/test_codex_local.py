import tempfile
import unittest
import json
from pathlib import Path

from archive_mcp.codex_local import import_file
from archive_mcp.db import connect, search


FIXTURE = Path(__file__).parents[1] / "fixtures" / "codex_session.jsonl"


class CodexLocalImportTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.connection = connect(Path(self.temp.name) / "archive.sqlite")

    def tearDown(self):
        self.connection.close()
        self.temp.cleanup()

    def test_import_keeps_dialogue_only_and_is_idempotent(self):
        self.assertEqual(import_file(self.connection, FIXTURE, "personal"), {
            "conversations": 1,
            "nodes": 2,
        })
        import_file(self.connection, FIXTURE, "personal")

        rows = self.connection.execute(
            "SELECT role, text, parent_source_id FROM messages ORDER BY created_at"
        ).fetchall()
        self.assertEqual(len(rows), 2)
        self.assertEqual(tuple(rows[0]), ("user", "How should the archive store sessions?", None))
        self.assertEqual(tuple(rows[1]), ("assistant", "Store normalized text in SQLite.", "line:3"))
        self.assertEqual(self.connection.execute(
            "SELECT kind FROM conversations"
        ).fetchone()[0], "local_session")
        self.assertEqual(search(self.connection, "intermediate"), [])
        self.assertEqual(search(self.connection, "metadata"), [])

    def test_excludes_review_transcript_sessions(self):
        source = Path(self.temp.name) / "review-session.jsonl"
        rows = [
            {
                "timestamp": "2025-01-02T15:04:05Z", "type": "session_meta",
                "payload": {"id": "review-session", "timestamp": "2025-01-02T15:04:05Z", "cwd": "/example"},
            },
            {
                "timestamp": "2025-01-02T15:04:06Z", "type": "response_item",
                "payload": {"type": "message", "role": "user", "content": [{
                    "type": "input_text", "text": "The following is the Codex agent history whose request action you are assessing."
                }], "internal_chat_message_metadata_passthrough": {"content_item_kinds": ["user.text"]}},
            },
            {
                "timestamp": "2025-01-02T15:04:07Z", "type": "response_item",
                "payload": {"type": "message", "role": "assistant", "phase": "final_answer", "content": [{
                    "type": "output_text", "text": "Review result should not be indexed."
                }]},
            },
            {
                "timestamp": "2025-01-02T15:04:08Z", "type": "response_item",
                "payload": {"type": "message", "role": "user", "content": [{
                    "type": "input_text", "text": "Keep this ordinary request."
                }], "internal_chat_message_metadata_passthrough": {"content_item_kinds": ["user.text"]}},
            },
            {
                "timestamp": "2025-01-02T15:04:09Z", "type": "response_item",
                "payload": {"type": "message", "role": "assistant", "phase": "final_answer", "content": [{
                    "type": "output_text", "text": "Keep the ordinary answer."
                }]},
            },
        ]
        source.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
        result = import_file(self.connection, source, "personal")
        self.assertEqual(result, {
            "conversations": 0, "nodes": 0, "excluded_review_sessions": 1,
        })
        self.assertEqual(search(self.connection, "Review result"), [])
        self.assertEqual(search(self.connection, "ordinary answer"), [])
        self.assertEqual(self.connection.execute("SELECT count(*) FROM conversations").fetchone()[0], 0)

    def test_rebuilds_stale_session_rows_on_reimport(self):
        result = import_file(self.connection, FIXTURE, "personal")
        self.assertEqual(result["nodes"], 2)
        # Simulate an older derived snapshot that indexed the review message;
        # re-import must remove it even though the source file is unchanged.
        conversation = self.connection.execute(
            "SELECT id FROM conversations WHERE source_id = 'codex-session-1'"
        ).fetchone()[0]
        self.connection.execute(
            "INSERT INTO messages(conversation_id,node_source_id,role,text,created_at) VALUES (?,?,?,?,?)",
            (conversation, "stale-review", "user", "stale review row", 1),
        )
        self.connection.commit()
        self.assertEqual(search(self.connection, '"stale review"')[0]["record_id"], "stale-review")
        import_file(self.connection, FIXTURE, "personal")
        self.assertEqual(search(self.connection, '"stale review"'), [])
        rows = self.connection.execute(
            "SELECT node_source_id,parent_source_id FROM messages WHERE conversation_id=? ORDER BY id",
            (conversation,),
        ).fetchall()
        self.assertEqual([tuple(row) for row in rows], [("line:3", None), ("line:7", "line:3")])


if __name__ == "__main__":
    unittest.main()
