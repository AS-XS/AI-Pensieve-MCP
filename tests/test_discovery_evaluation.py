import copy
import json
import tempfile
import unittest
from pathlib import Path

from archive_mcp.discovery_evaluate import (
    ANSWER_SCHEMA, CASES, REQUIRED_EVIDENCE, corpus, larger_corpus, passages, prepare, score_answer, score_trace,
)


def answer():
    return {"answer": "Synthetic answer", "findings": [], "coverage": {
        "complete": False, "examined_sources": [],
        "unexamined_sources": [dict(provider=p, account=a) for p, a in
                               sorted({(r['provider'], r['account']) for r in corpus()})],
        "limitations": "Partial read", "resume": [],
    }}


class DiscoveryEvaluationTest(unittest.TestCase):
    def test_larger_layouts_preserve_gold_and_vary_evidence_positions(self):
        records = larger_corpus(11)
        self.assertEqual(records, larger_corpus(11))
        self.assertNotEqual(records, larger_corpus(29))
        self.assertEqual(len(records), 1000)
        self.assertEqual(len({(r['provider'], r['account']) for r in records}), 8)
        identities = {tuple(r[k] for k in ('provider', 'account', 'conversation_id', 'record_id')) for r in records}
        self.assertEqual(len(identities), 1000)
        self.assertTrue(REQUIRED_EVIDENCE['nlp'] <= identities)
        self.assertTrue(REQUIRED_EVIDENCE['projects'] <= identities)
        self.assertGreater(sum(len(r['text']) for r in records), 24000 * 10)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(prepare(root, seed=11)['records'], 1000)
            self.assertEqual(json.loads((root / 'corpus.json').read_text()), records)

    def test_trace_scores_selected_corpus_instead_of_small_default(self):
        records = larger_corpus(11)
        result = answer()
        result['coverage']['unexamined_sources'] = [dict(provider=p, account=a) for p, a in
                                                   sorted({(r['provider'], r['account']) for r in records})]
        score = score_trace('nlp', result, [], [], {'started_at_epoch': 0, 'elapsed_seconds': 1}, records)
        self.assertEqual(score['total_records'], 1000)
        self.assertEqual(score['total_body_characters'], sum(len(r['text']) for r in records))
        self.assertTrue(score['source_coverage_report_accurate'])

    def test_prepare_is_synthetic_and_does_not_overwrite_existing_database(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = prepare(root)
            self.assertEqual(result, {"records": 39, "sources": 4, "cases": list(CASES)})
            self.assertEqual(json.loads((root / 'answer.schema.json').read_text()), ANSWER_SCHEMA)
            with self.assertRaises(FileExistsError):
                prepare(root)

    def test_citations_require_correct_account_identity_and_exact_quote(self):
        result = answer()
        evidence = dict(provider="chatgpt", account="personal", conversation_id="syntax-study",
                        record_id="syntax-done", quote="I ran the evaluation and wrote the error analysis.")
        result['findings'] = [dict(claim="Completed research", classification="completed_work", evidence=[evidence])]
        score = score_answer('nlp', result)
        self.assertEqual(score['invalid_citations'], 0)
        self.assertEqual(score['required_evidence_cited'], 1)
        evidence['account'] = 'work'
        self.assertEqual(score_answer('nlp', result)['invalid_citations'], 1)
        evidence['account'] = 'personal'
        evidence['quote'] = 'Invented quotation'
        self.assertEqual(score_answer('nlp', result)['invalid_citations'], 1)

    def test_full_read_and_call_budget_are_measured_from_trace_not_claims(self):
        record = next(r for r in corpus() if r['record_id'] == 'syntax-done')
        result = answer()
        result['coverage']['complete'] = True
        call = dict(type='item.completed', item=dict(type='mcp_tool_call', server='pensieve_eval',
                    tool='get_message', result={'structured_content': {
                        **record, 'node_source_id': record['record_id'],
                    }, 'content': [{'type': 'text', 'text': json.dumps(record)}]}, status='completed'))
        events = [copy.deepcopy(call) for _ in range(13)]
        score = score_trace('nlp', result, events, [], {'started_at_epoch': 0, 'elapsed_seconds': 1})
        self.assertEqual(score['fully_read_records'], 1)
        self.assertEqual(score['body_and_snippet_characters'], len(record['text']) * 13)
        self.assertFalse(score['complete_coverage_claim_supported'])
        self.assertFalse(score['within_call_and_character_budget'])
        self.assertTrue(score['semantic_review_required'])

    def test_nested_conversation_and_comparison_provenance(self):
        data = {'conversation': {'provider': 'claude', 'account': 'personal', 'source_id': 'c'},
                'messages': [{'node_source_id': 'm', 'text': 'original'}]}
        rows = list(passages(data))
        self.assertEqual(rows, [({'provider': 'claude', 'account': 'personal', 'conversation_id': 'c'},
                                 'm', 'text', 'original', 0)])
        data = {'bundles': [{'evidence': [{'provenance': rows[0][0], 'record_id': 'm', 'snippet': 'excerpt'}]}]}
        self.assertEqual(list(passages(data))[0][0], rows[0][0])
        data = {'provider': 'claude', 'account': 'personal', 'source_id': 'memory', 'text': 'note'}
        self.assertEqual(list(passages(data))[0][1], 'memory')

    def test_empty_trace_is_not_complete_or_a_successful_read(self):
        result = answer()
        result['coverage']['complete'] = True
        score = score_trace('partial', result, [], [], {'started_at_epoch': 0, 'elapsed_seconds': 1})
        self.assertFalse(score['complete_coverage_claim_supported'])
        self.assertFalse(score['within_read_time_budget'])
        self.assertEqual(score['fully_read_records'], 0)
