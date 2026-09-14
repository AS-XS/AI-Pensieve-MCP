import json
import tempfile
import unittest
from pathlib import Path

from import_expectations import expected_result

from archive_mcp.db import connect, integrity_status, search
from archive_mcp.auto_import import detect
from archive_mcp.qwen_code import import_file


FIXTURE = Path(__file__).parents[1] / "fixtures" / "qwen_code.jsonl"


class QwenCodeImportTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.connection = connect(Path(self.temp.name) / "archive.sqlite")

    def tearDown(self):
        self.connection.close()
        self.temp.cleanup()

    def test_imports_dialogue_branches_only_and_is_idempotent(self):
        expected = {"conversations": 1, "nodes": 6}
        self.assertEqual(import_file(self.connection, FIXTURE, "personal"), expected_result(expected))
        self.assertEqual(import_file(self.connection, FIXTURE, "personal"), expected_result(expected, state='unchanged'))

        rows = self.connection.execute(
            "SELECT node_source_id, parent_source_id FROM messages ORDER BY created_at"
        ).fetchall()
        self.assertEqual([tuple(row) for row in rows], [
            ("user-1", None),
            ("assistant-1", "user-1"),
            ("user-2", "assistant-1"),
            ("assistant-2", "user-2"),
            ("user-branch", "assistant-1"),
            ("assistant-branch", "user-branch"),
        ])
        self.assertEqual(search(self.connection, "Qwen")[0]["provider"], "qwen-code")
        for marker in (
            "privatefilemarker", "privateattachmentmarker",
            "hiddentoolinputmarker", "hiddentooloutputmarker",
        ):
            self.assertEqual(search(self.connection, marker), [])
        self.assertTrue(integrity_status(self.connection)["ok"])

    def test_json_export_and_hidden_thoughts(self):
        source = Path(self.temp.name) / "export.json"
        source.write_text(json.dumps({
            "sessionId": "qwen-json-session",
            "startTime": "2025-01-02T15:04:05Z",
            "metadata": {"cwd": "/example/project"},
            "messages": [
                {
                    "uuid": "user-1", "parentUuid": None,
                    "timestamp": "2025-01-02T15:04:05Z", "type": "user",
                    "message": {"role": "user", "content": "Visible JSON prompt"},
                },
                {
                    "uuid": "assistant-1", "parentUuid": "user-1",
                    "timestamp": "2025-01-02T15:04:06Z", "type": "assistant",
                    "message": {"role": "model", "parts": [
                        {"text": "hiddenreasoningmarker", "thought": True},
                        {"text": "Visible JSON answer"},
                    ]},
                },
            ],
        }), encoding="utf-8-sig")

        self.assertEqual(detect(source), "qwen-code")
        self.assertEqual(import_file(self.connection, source), expected_result({
            "conversations": 1, "nodes": 2,
        }))
        self.assertEqual(search(self.connection, "hiddenreasoningmarker"), [])
        self.assertEqual(len(search(self.connection, '"Visible JSON"')), 2)

    def test_native_jsonl_session(self):
        source = Path(self.temp.name) / "native.jsonl"
        rows = [
            {
                "uuid": "system-1", "parentUuid": None,
                "sessionId": "qwen-native-session",
                "timestamp": "2025-01-02T15:04:04Z", "type": "system",
                "cwd": "/example/project", "version": "1.0.0",
            },
            {
                "uuid": "user-1", "parentUuid": "system-1",
                "sessionId": "qwen-native-session",
                "timestamp": "2025-01-02T15:04:05Z", "type": "user",
                "cwd": "/example/project", "version": "1.0.0",
                "message": {"role": "user", "parts": [{"text": "Native prompt"}]},
            },
            {
                "uuid": "assistant-1", "parentUuid": "user-1",
                "sessionId": "qwen-native-session",
                "timestamp": "2025-01-02T15:04:06Z", "type": "assistant",
                "cwd": "/example/project", "version": "1.0.0",
                "message": {"role": "model", "parts": [
                    {"text": "nativeresoningmarker", "thought": True},
                    {"text": "Native answer"},
                ]},
            },
            {
                "uuid": "tool-1", "parentUuid": "assistant-1",
                "sessionId": "qwen-native-session",
                "timestamp": "2025-01-02T15:04:07Z", "type": "tool_result",
                "cwd": "/example/project", "version": "1.0.0",
                "message": {"role": "user", "parts": [{
                    "functionResponse": {"response": {"output": "nativetoolmarker"}},
                }]},
            },
            {
                "uuid": "assistant-2", "parentUuid": "tool-1",
                "sessionId": "qwen-native-session",
                "timestamp": "2025-01-02T15:04:08Z", "type": "assistant",
                "cwd": "/example/project", "version": "1.0.0",
                "message": {"role": "model", "parts": [{"text": "Done"}]},
            },
        ]
        source.write_text(
            "\n".join(json.dumps(row) for row in rows), encoding="utf-8",
        )

        self.assertEqual(detect(source), "qwen-code")
        self.assertEqual(import_file(self.connection, source), expected_result({
            "conversations": 1, "nodes": 3,
        }))
        parent = self.connection.execute(
            "SELECT parent_source_id FROM messages WHERE node_source_id = 'assistant-2'"
        ).fetchone()[0]
        self.assertEqual(parent, "assistant-1")
        self.assertEqual(search(self.connection, "nativeresoningmarker"), [])
        self.assertEqual(search(self.connection, "nativetoolmarker"), [])

    def test_empty_and_malformed_exports(self):
        empty = Path(self.temp.name) / "empty.json"
        empty.write_text(json.dumps({
            "sessionId": "qwen-empty",
            "startTime": "2025-01-02T15:04:05Z",
            "messages": [],
        }), encoding="utf-8")
        self.assertEqual(import_file(self.connection, empty), expected_result({
            "conversations": 1, "nodes": 0,
        }))

        malformed = Path(self.temp.name) / "malformed.jsonl"
        malformed.write_text("{", encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            import_file(self.connection, malformed)


if __name__ == "__main__":
    unittest.main()
