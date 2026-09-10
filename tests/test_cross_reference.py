import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from archive_mcp.chatgpt import import_file as import_chatgpt
from archive_mcp.claude import import_file as import_claude
from archive_mcp.db import connect, cross_reference, initialize, timestamp
from archive_mcp.importing import account_id, conversation_id, upsert_message


FIXTURES = Path(__file__).parents[1] / "fixtures"


class CrossReferenceTest(unittest.TestCase):
    def test_bundles_are_provider_account_attributed_and_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            with closing(connect(Path(directory) / "archive.sqlite")) as connection:
                import_chatgpt(connection, FIXTURES / "chatgpt.json", "personal")
                import_claude(connection, FIXTURES / "claude.json", "personal")
                result = cross_reference(connection, "archive", candidate_limit=3)
                self.assertEqual(result["candidate_limit"], 3)
                self.assertEqual(result["candidates_examined"], 6)
                self.assertEqual(result["candidate_limit_scope"], "per_source")
                self.assertTrue(result["candidate_limit_reached"])
                self.assertEqual(
                    {(b["provider"], b["account"]) for b in result["bundles"]},
                    {("chatgpt", "personal"), ("claude", "personal")},
                )
                for bundle in result["bundles"]:
                    self.assertLessEqual(len(bundle["evidence"]), 5)
                    self.assertTrue(bundle["conversations"])
                    for evidence in bundle["evidence"]:
                        self.assertEqual(evidence["provenance"]["provider"], bundle["provider"])
                        self.assertEqual(evidence["provenance"]["account"], bundle["account"])
                        self.assertNotIn("source_file", str(evidence))
                        self.assertNotIn("text", evidence)

    def test_filters_and_limit_are_explicit(self):
        with closing(connect(":memory:")) as connection:
            import_chatgpt(connection, FIXTURES / "chatgpt.json", "one")
            import_chatgpt(connection, FIXTURES / "chatgpt.json", "two")
            result = cross_reference(
                connection, "SQLite", accounts=["two"], limit=1, candidate_limit=1,
            )
            self.assertEqual(len(result["bundles"]), 1)
            self.assertEqual(result["bundles"][0]["account"], "two")
            self.assertEqual(result["sources_unexamined"], 0)

    def test_busy_source_cannot_crowd_out_another_provider_or_account(self):
        with closing(connect(":memory:")) as connection:
            initialize(connection)
            for provider, account, count in (("example-a", "one", 20),
                                             ("example-a", "two", 1),
                                             ("example-b", "one", 1)):
                source = account_id(connection, provider, account)
                conversation = conversation_id(connection, source, "same-id", "synthetic", "Test", 1, 1)
                for index in range(count):
                    upsert_message(connection, conversation, str(index), str(index), None,
                                   "user", "needle", 1)
            result = cross_reference(connection, "needle", candidate_limit=10)
            self.assertEqual(result["sources_examined"], 3)
            self.assertEqual(result["candidates_examined"], 12)
            self.assertEqual([b["matched_records"] for b in result["bundles"]], [10, 1, 1])
            self.assertEqual([b["candidate_limit_reached"] for b in result["bundles"]], [True, False, False])
            self.assertEqual([len(b["evidence"]) for b in result["bundles"]], [5, 1, 1])
            self.assertEqual(result["bundles"][0]["evidence_omitted"], 5)
            self.assertEqual(result["bundles"][0]["conversation_count"], 1)

    def test_no_matches_are_distinct_from_unexamined_sources(self):
        with closing(connect(":memory:")) as connection:
            import_chatgpt(connection, FIXTURES / "chatgpt.json", "one")
            import_claude(connection, FIXTURES / "claude.json", "two")
            result = cross_reference(connection, "nonexistent", limit=1)
            self.assertEqual(result["sources_available"], 2)
            self.assertEqual(result["sources_examined"], 1)
            self.assertEqual(result["sources_unexamined"], 1)
            self.assertEqual(result["bundles"][0]["status"], "no_matches")
            self.assertEqual(result["bundles"][0]["evidence"], [])
            self.assertFalse(result["candidate_limit_reached"])
            remaining = cross_reference(connection, "SQLite", providers=["claude"], accounts=["two"])
            self.assertEqual(remaining["sources_unexamined"], 0)
            self.assertEqual(remaining["bundles"][0]["status"], "matches")
            empty = cross_reference(connection, "SQLite", accounts=["absent"])
            self.assertEqual(empty["sources_available"], 0)
            self.assertEqual(empty["bundles"], [])

    def test_dates_filter_evidence_without_hiding_no_match_sources(self):
        with closing(connect(":memory:")) as connection:
            import_chatgpt(connection, FIXTURES / "chatgpt.json", "personal")
            import_claude(connection, FIXTURES / "claude.json", "personal")
            result = cross_reference(connection, "archive", date_from=timestamp("2024-01-01"),
                                     date_to=timestamp("2024-01-01", end=True))
            self.assertEqual([b["status"] for b in result["bundles"]], ["no_matches", "matches"])
            self.assertTrue(all(e["created_at"].startswith("2024-01-01")
                                for e in result["bundles"][1]["evidence"]))


if __name__ == "__main__":
    unittest.main()
