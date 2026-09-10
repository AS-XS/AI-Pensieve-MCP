import io
import json
import tempfile
import unittest
from contextlib import closing, redirect_stderr, redirect_stdout
from pathlib import Path

from archive_mcp.db import connect, get_conversation, search
from archive_mcp.evaluate import FIXTURES, evaluate, main, seed_corpus


class EvaluationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "archive.sqlite"
        self.cases = json.loads((FIXTURES / "retrieval_cases.json").read_text())
        with closing(connect(self.database)) as connection:
            seed_corpus(connection, json.loads((FIXTURES / "retrieval_corpus.json").read_text()))

    def tearDown(self):
        self.temp.cleanup()

    def test_baseline_records_successes_and_known_search_gaps(self):
        with closing(connect(self.database, read_only=True)) as connection:
            result = evaluate(connection, self.cases)
            title = search(connection, self.cases[9]["query"])[0]
            page = get_conversation(
                connection, title["provider"], title["account"], title["conversation_id"]
            )
            self.assertEqual(page["messages"][0]["node_source_id"], "milestone")
            self.assertEqual(connection.total_changes, 0)
        self.assertEqual(result["case_count"], 11)
        self.assertEqual(result["positive_cases"], 10)
        self.assertEqual(result["hit_rate"], 0.9)
        self.assertEqual(result["mean_recall"], 0.9)
        self.assertEqual(result["correct_empty_results"], 1)
        self.assertEqual([row["case"] for row in result["cases"] if not row["passed"]], [9])
        # At k=1, the two-record comparison cannot have full recall.
        with closing(connect(self.database, read_only=True)) as connection:
            limited = evaluate(connection, [self.cases[2]], limit=1)
        self.assertEqual(limited["mean_recall"], 0.5)
        self.assertEqual(limited["mean_reciprocal_rank"], 1.0)

    def test_stale_gold_label_is_not_reported_as_a_search_miss(self):
        self.cases[0]["expected"][0]["record_id"] = "missing"
        with closing(connect(self.database, read_only=True)) as connection:
            with self.assertRaisesRegex(ValueError, "Case 1: expected record does not exist"):
                evaluate(connection, self.cases)

    def test_cli_reports_only_metrics_even_for_private_cases(self):
        casefile = Path(self.temp.name) / "private-cases.json"
        private_case = self.cases[0]
        private_case["question"] = "PRIVATE_QUESTION"
        private_case["query"] = "PRIVATE_QUERY"
        casefile.write_text(json.dumps([private_case]))
        output = io.StringIO()
        with redirect_stdout(output):
            main(["--database", str(self.database), "--cases", str(casefile)])
        self.assertFalse(json.loads(output.getvalue())["cases"][0]["passed"])
        for secret in ("PRIVATE_QUESTION", "PRIVATE_QUERY", "archive-design", "personal", str(casefile)):
            self.assertNotIn(secret, output.getvalue())
        private_case["query"] = '"INVALID_PRIVATE_QUERY'
        casefile.write_text(json.dumps([private_case]))
        error = io.StringIO()
        with redirect_stderr(error), self.assertRaises(SystemExit) as raised:
            main(["--database", str(self.database), "--cases", str(casefile)])
        self.assertEqual(raised.exception.code, 2)
        self.assertEqual(error.getvalue(), "Evaluation failed (ValueError)\n")


if __name__ == "__main__":
    unittest.main()
