import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from import_expectations import expected_result

from archive_mcp.antigravity import import_file
from archive_mcp.db import connect, search


def varint(value):
    encoded = bytearray()
    while value > 127:
        encoded.append((value & 127) | 128)
        value >>= 7
    encoded.append(value)
    return bytes(encoded)


def scalar(number, value):
    return varint(number << 3) + varint(value)


def message(number, value):
    return varint(number << 3 | 2) + varint(len(value)) + value


def step(step_type, container, text, seconds):
    timestamp = message(1, scalar(1, seconds))
    body = message(container, message(2 if step_type == 14 else 1, text.encode()))
    return scalar(1, step_type) + scalar(4, 3) + message(5, timestamp) + body


def create_source(path):
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.executescript("""
            CREATE TABLE trajectory_meta(trajectory_id TEXT PRIMARY KEY, cascade_id TEXT);
            CREATE TABLE trajectory_metadata_blob(id TEXT PRIMARY KEY, data BLOB);
            CREATE TABLE steps(
                idx INTEGER PRIMARY KEY, step_type INTEGER, status INTEGER, step_payload BLOB
            );
        """)
        connection.execute(
            "INSERT INTO trajectory_meta VALUES (?, ?)", ("trajectory-1", "cascade-1")
        )
        workspace = message(1, message(1, b"file:///example/local-archive"))
        connection.execute("INSERT INTO trajectory_metadata_blob VALUES ('main', ?)", (workspace,))
        connection.executemany("INSERT INTO steps VALUES (?, ?, 3, ?)", [
            (1, 14, step(14, 19, "How should Antigravity history be stored?", 1735830245)),
            (2, 8, scalar(1, 8) + scalar(4, 3)),
            (3, 15, step(15, 20, "Store normalized dialogue in SQLite.", 1735830246)),
        ])


class AntigravityImportTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.source = root / "conversation.db"
        create_source(self.source)
        self.connection = connect(root / "archive.sqlite")

    def tearDown(self):
        self.connection.close()
        self.temp.cleanup()

    def test_import_keeps_dialogue_only_and_is_idempotent(self):
        self.assertEqual(import_file(self.connection, self.source, "personal"), expected_result({
            "conversations": 1,
            "nodes": 2,
        }))
        import_file(self.connection, self.source, "personal")

        rows = self.connection.execute(
            "SELECT role, parent_source_id FROM messages ORDER BY created_at"
        ).fetchall()
        self.assertEqual([tuple(row) for row in rows], [
            ("user", None), ("assistant", "step:1"),
        ])
        result = search(self.connection, "normalized")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["provider"], "antigravity")


if __name__ == "__main__":
    unittest.main()
