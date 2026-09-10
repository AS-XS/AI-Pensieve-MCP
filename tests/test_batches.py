import tempfile
import unittest
from pathlib import Path

from archive_mcp.batches import import_report, run_batch
from archive_mcp.db import connect


class ImportBatchTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.connection = connect(Path(self.temp.name) / "archive.sqlite")

    def tearDown(self):
        self.connection.close()
        self.temp.cleanup()

    def test_failed_import_records_safe_warning(self):
        source = Path(self.temp.name) / "synthetic.json"

        def fail(connection, path, account):
            raise ValueError("private message must not enter warning details")

        with self.assertRaises(ValueError):
            run_batch(
                self.connection,
                [("synthetic", source, fail)],
                "personal",
                "auto",
            )

        report = import_report(self.connection)
        self.assertEqual(report[0]["status"], "failed")
        self.assertEqual(report[0]["warnings"], {"import_failed": 1})
        self.assertNotIn("account", report[0])
        self.assertNotIn(str(source), str(report))
        warning = self.connection.execute(
            "SELECT source_format, detail FROM import_warnings"
        ).fetchone()
        self.assertEqual(tuple(warning), ("synthetic", "ValueError"))

    def test_empty_import_is_reported(self):
        source = Path(self.temp.name) / "empty.json"

        def empty(connection, path, account):
            return {"conversations": 1, "nodes": 0}

        result = run_batch(
            self.connection,
            [("synthetic", source, empty)],
            "personal",
            "auto",
        )
        self.assertEqual(result["warnings"], {"no_indexable_records": 1})
        self.assertEqual(import_report(self.connection)[0]["warning_count"], 1)

    def test_excluded_review_session_is_reported_without_source_details(self):
        source = Path(self.temp.name) / "review.jsonl"

        def excluded(connection, path, account):
            return {"conversations": 0, "nodes": 0, "excluded_review_sessions": 1}

        result = run_batch(
            self.connection,
            [("codex", source, excluded)],
            "personal",
            "refresh",
        )
        self.assertEqual(result["warnings"], {
            "excluded_review_session": 1,
            "no_indexable_records": 1,
        })
        warning_codes = [row[0] for row in self.connection.execute(
            "SELECT code FROM import_warnings ORDER BY id"
        )]
        self.assertEqual(warning_codes, ["excluded_review_session", "no_indexable_records"])
        self.assertNotIn(str(source), str(import_report(self.connection)))


if __name__ == "__main__":
    unittest.main()
