import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from archive_mcp.chatgpt import import_file as import_chatgpt
from archive_mcp.claude import import_file as import_claude
from archive_mcp.db import connect, list_conversations, timestamp


FIXTURES = Path(__file__).parents[1] / "fixtures"


class EnumerationTest(unittest.TestCase):
    def test_pages_cover_an_unchanged_archive_without_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            with closing(connect(Path(directory) / "archive.sqlite")) as connection:
                import_chatgpt(connection, FIXTURES / "chatgpt.json", "personal")
                import_claude(connection, FIXTURES / "claude.json", "personal")
                first = list_conversations(connection, limit=1)
                self.assertEqual(len(first["conversations"]), 1)
                self.assertTrue(first["has_more"])
                self.assertIsNotNone(first["next_cursor"])
                self.assertEqual(first["freshness_policy"], "restart_after_import_refresh_or_rebuild")
                self.assertNotIn("snapshot_max_id", first)
                second = list_conversations(
                    connection, limit=5, cursor=first["next_cursor"],
                )
                self.assertFalse(second["has_more"])
                self.assertIsNone(second["next_cursor"])
                self.assertEqual(
                    {row["conversation_id"] for row in first["conversations"] + second["conversations"]},
                    {"conversation-1", "claude-conversation-1"},
                )
                self.assertTrue(all("text" not in row for row in second["conversations"]))
                self.assertEqual(len(first["conversations"] + second["conversations"]), 2)

    def test_restart_after_replacement_with_reused_row_ids(self):
        with closing(connect(":memory:")) as connection:
            import_chatgpt(connection, FIXTURES / "chatgpt.json", "before")
            import_claude(connection, FIXTURES / "claude.json", "before")
            first = list_conversations(connection, limit=1)
            old_max = connection.execute("SELECT max(id) FROM conversations").fetchone()[0]
            with connection:
                connection.execute("DELETE FROM conversations")
            import_chatgpt(connection, FIXTURES / "chatgpt.json", "after")
            new_id = connection.execute("SELECT id FROM conversations").fetchone()[0]
            self.assertLessEqual(new_id, old_max)
            # An old cursor can miss replacement data; the advertised policy is to restart.
            self.assertEqual(list_conversations(connection, cursor=first["next_cursor"])["conversations"], [])
            restarted = list_conversations(connection, cursor=0)
            self.assertEqual([r["account"] for r in restarted["conversations"]], ["after"])
            self.assertIsNone(restarted["next_cursor"])
            import_claude(connection, FIXTURES / "claude.json", "later")
            with connection:
                connection.execute("UPDATE conversations SET title = 'Updated synthetic title'")
            restarted = list_conversations(connection)
            self.assertEqual({r["account"] for r in restarted["conversations"]}, {"after", "later"})
            self.assertTrue(all(r["title"] == "Updated synthetic title" for r in restarted["conversations"]))

    def test_filters_and_date_range_apply_to_conversations(self):
        with closing(connect(":memory:")) as connection:
            import_chatgpt(connection, FIXTURES / "chatgpt.json", "personal")
            result = list_conversations(
                connection, providers=["chatgpt"], accounts=["personal"],
                date_from=timestamp("2023-11-14T00:00:00+00:00"),
                date_to=timestamp("2023-11-14T23:59:59+00:00"),
            )
            self.assertEqual(len(result["conversations"]), 1)
            self.assertEqual(result["conversations"][0]["message_count"], 4)
            self.assertEqual(list_conversations(connection, providers=["claude"])["conversations"], [])


if __name__ == "__main__":
    unittest.main()
