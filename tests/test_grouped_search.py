import tempfile
import unittest
from pathlib import Path

from archive_mcp.db import (
    connect, get_conversation_matches, get_message_context, initialize,
    search, search_conversations,
)
from archive_mcp.importing import account_id, conversation_id, upsert_memory, upsert_message


class GroupedSearchTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "archive.sqlite"
        self.connection = connect(self.database)
        initialize(self.connection)

    def tearDown(self):
        self.connection.close()
        self.temp.cleanup()

    def add_thread(self, source, count, provider="example", account="personal", title="Discussion"):
        aid = account_id(self.connection, provider, account)
        cid = conversation_id(self.connection, aid, source, "synthetic", title, 100, 999)
        for i in range(count):
            upsert_message(
                self.connection, cid, f"message-{i:03}", None,
                f"message-{i-1:03}" if i else None, "assistant", "Orchid", 200 + i,
            )
        self.connection.commit()

    def test_grouping_exposes_threads_hidden_by_repeated_messages(self):
        self.add_thread("a-busy", 8)
        self.add_thread("b-other", 1)
        self.add_thread("c-other", 1)
        raw = search(self.connection, "Orchid", limit=5)
        self.assertEqual({r["conversation_id"] for r in raw}, {"a-busy"})
        grouped = search_conversations(self.connection, "Orchid", limit=3)
        self.assertEqual([g["conversation_id"] for g in grouped["groups"]], [
            "a-busy", "b-other", "c-other",
        ])
        first = grouped["groups"][0]
        self.assertEqual(first["candidate_matches"], 8)
        self.assertEqual(len(first["matches"]), 3)
        hit = first["matches"][0]
        context = get_message_context(
            self.connection, first["provider"], first["account"],
            first["conversation_id"], hit["record_id"],
        )
        self.assertEqual(context["message"]["text"], "Orchid")
        self.assertEqual(search_conversations(self.connection, "Orchid", limit=1)["groups_omitted"], 2)

    def test_provider_accounts_titles_and_memories_keep_separate_identities(self):
        for provider, account in (("example", "personal"), ("example", "work"), ("other", "personal")):
            self.add_thread("shared-id", 1, provider, account, title="Orchid")
        aid = account_id(self.connection, "example", "personal")
        for mid in ("shared-id", "second-memory"):
            upsert_memory(self.connection, aid, mid, "synthetic", "note", "Orchid", "Orchid", 250)
        self.connection.commit()
        grouped = search_conversations(self.connection, "Orchid")
        self.assertEqual(len(grouped["groups"]), 5)
        threads = [g for g in grouped["groups"] if g["group_type"] == "conversation"]
        self.assertEqual(len(threads), 3)
        for group in threads:
            self.assertEqual({r["record_type"] for r in group["matches"]}, {"message", "conversation"})
        scoped = get_conversation_matches(self.connection, "Orchid", "example", "personal", "shared-id")
        self.assertEqual({r["record_type"] for r in scoped["matches"]}, {"message", "conversation"})
        self.assertTrue(all(r["provider"] == "example" and r["account"] == "personal" for r in scoped["matches"]))

    def test_expansion_pages_beyond_global_candidate_limit(self):
        self.add_thread("busy", 63)
        self.connection.close()
        self.connection = connect(self.database, read_only=True)
        grouped = search_conversations(self.connection, "Orchid")
        self.assertTrue(grouped["candidate_limit_reached"])
        self.assertEqual(grouped["candidates_examined"], 50)
        self.assertEqual(grouped["groups"][0]["candidate_matches"], 50)
        first = get_conversation_matches(self.connection, "Orchid", "example", "personal", "busy", limit=50)
        second = get_conversation_matches(self.connection, "Orchid", "example", "personal", "busy", offset=first["next_offset"], limit=50)
        self.assertEqual(len(first["matches"]), 50)
        self.assertEqual(len(second["matches"]), 13)
        self.assertIsNone(second["next_offset"])
        self.assertEqual(len({r["record_id"] for r in first["matches"] + second["matches"]}), 63)
        end = get_conversation_matches(self.connection, "Orchid", "example", "personal", "busy", offset=63)
        self.assertEqual(end, {"matches": [], "next_offset": None})
        self.assertEqual(self.connection.total_changes, 0)

    def test_filters_are_replayed_and_empty_matches_are_distinct_from_missing_thread(self):
        self.add_thread("same", 4, title="Orchid")
        self.add_thread("same", 4, account="work", title="Orchid")
        grouped = search_conversations(
            self.connection, "Orch*", providers=["example"], accounts=["personal"],
            date_from=201, date_to=202, limit=1,
        )
        self.assertEqual(len(grouped["groups"]), 1)
        group = grouped["groups"][0]
        self.assertEqual(group["candidate_matches"], 2)
        page = get_conversation_matches(
            self.connection, "Orch*", "example", "personal", "same",
            date_from=201, date_to=202,
        )
        self.assertEqual(page["matches"], group["matches"])
        self.assertEqual(get_conversation_matches(
            self.connection, "missing", "example", "personal", "same"
        ), {"matches": [], "next_offset": None})
        self.assertEqual(search_conversations(self.connection, "missing")["groups"], [])
        with self.assertRaises(LookupError):
            get_conversation_matches(self.connection, "Orchid", "example", "missing", "same")


if __name__ == "__main__":
    unittest.main()
