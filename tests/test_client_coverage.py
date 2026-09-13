import asyncio
import json
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from mcp import Client
from mcp.client.stdio import StdioServerParameters, stdio_client

from archive_mcp.client_coverage import CoverageLedger, coverage_from_events
from archive_mcp.db import connect
from archive_mcp.discovery_evaluate import corpus
from archive_mcp.evaluate import seed_corpus
from archive_mcp.mcp_server import create_server


SOURCES = [dict(provider='a', account='personal'), dict(provider='b', account='work')]


class ClientCoverageTest(unittest.TestCase):
    def test_search_without_matches_is_separate_from_text_and_failed_attempts(self):
        ledger = CoverageLedger()
        ledger.record('list_sources', {}, {'result': SOURCES})
        ledger.record('cross_reference', {}, {'bundles': [dict(s, evidence=[]) for s in SOURCES]})
        ledger.record('survey_archive', {'max_records': 80}, failed=True)
        ledger.record('search_history', {'query': 'test'}, {'result': [dict(SOURCES[0], record_id='m', snippet='EVIDENCE_PAYLOAD')]})
        result = ledger.summary()
        self.assertEqual(result['attempted_calls'], 4)
        self.assertEqual(result['failed_calls'], 1)
        self.assertEqual(result['sources_searched'], SOURCES)
        self.assertEqual(result['sources_with_returned_text'], SOURCES[:1])
        self.assertEqual(result['known_sources_without_returned_text'], SOURCES[1:])
        self.assertFalse(result['complete_archive_traversal'])
        self.assertEqual(result['returned_text_characters'], len('EVIDENCE_PAYLOAD'))
        self.assertNotIn('EVIDENCE_PAYLOAD', json.dumps(result))  # No retrieved text retained in fields.

    def test_tail_page_date_scope_and_missing_page_cannot_claim_full_traversal(self):
        tail = dict(records=[], sources=[dict(s, status='complete') for s in SOURCES], next_cursor=None)
        ledger = CoverageLedger()
        ledger.record('survey_archive', {'cursor': 'unknown'}, tail)
        self.assertFalse(ledger.summary()['complete_archive_traversal'])
        self.assertEqual(ledger.summary()['sources_fully_traversed'], [])
        ledger.record('survey_archive', {'date_from': '2025-01-01'}, tail)
        self.assertFalse(ledger.summary()['complete_archive_traversal'])
        self.assertEqual(ledger.summary()['sources_fully_traversed'], [])
        ledger.record('survey_archive', {}, {**tail, 'next_cursor': 'first'})
        ledger.record('survey_archive', {'cursor': 'skipped'}, tail)
        self.assertFalse(ledger.summary()['complete_archive_traversal'])
        ledger.record('survey_archive', {'cursor': 'first'}, tail)
        self.assertTrue(ledger.summary()['complete_archive_traversal'])
        self.assertEqual(ledger.summary()['sources_fully_traversed'], SOURCES)

    def test_event_adapter_counts_rejections_and_unfinished_calls_once(self):
        def event(kind, identity, server='archive', **fields):
            return dict(type=kind, item=dict(type='mcp_tool_call', id=identity, server=server,
                                            tool='archive_status', arguments={}, **fields))
        done = event('item.completed', '1', status='failed')
        events = [event('item.started', '1'), done, done,
                  event('item.started', '2'), event('item.started', '3', server='other')]
        result = coverage_from_events(events, 'archive')
        self.assertEqual(result['attempted_calls'], 2)
        self.assertEqual(result['failed_calls'], 1)
        self.assertEqual(result['unfinished_calls'], 1)
        self.assertEqual(result['successful_results'], 0)

    def test_prompt_is_available_without_reading_or_creating_database(self):
        async def verify(path):
            async with Client(create_server(path)) as client:
                self.assertIn('discover_history', [p.name for p in (await client.list_prompts()).prompts])
                result = await client.get_prompt('discover_history', {'question': 'Which projects remain unfinished?'})
                text = result.messages[0].content.text
                self.assertIn('Which projects remain unfinished?', text)
                self.assertIn('survey_archive', text)
                self.assertIn('newest_first=true', text)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'absent.sqlite'
            asyncio.run(verify(path))
            self.assertFalse(path.exists())

    def test_real_stdio_accounting_matches_full_survey_and_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / 'synthetic.sqlite'
            with closing(connect(database)) as db:
                seed_corpus(db, corpus())
            params = StdioServerParameters(command=sys.executable,
                args=['-m', 'archive_mcp.mcp_server', str(database)],
                env={'PYTHONPATH': str(Path(__file__).resolve().parents[1] / 'src')}, cwd=directory)
            async def verify():
                ledger = CoverageLedger()
                async with Client(stdio_client(params), read_timeout_seconds=10) as client:
                    status = await client.call_tool('archive_status', {})
                    ledger.record('archive_status', {}, status.structured_content)
                    cursor = None
                    while True:
                        arguments = {'cursor': cursor, 'max_chars': 2000}
                        result = await client.call_tool('survey_archive', arguments)
                        self.assertFalse(result.is_error)
                        ledger.record('survey_archive', arguments, result.structured_content)
                        cursor = result.structured_content['next_cursor']
                        if cursor is None:
                            break
                summary = ledger.summary()
                self.assertTrue(summary['complete_archive_traversal'])
                self.assertEqual(summary['returned_text_characters'], sum(len(r['text']) for r in corpus()))
                self.assertEqual(summary['sources_fully_traversed'], summary['known_sources'])
                self.assertEqual(summary['known_sources_without_returned_text'], [])
                self.assertEqual(summary['inventory_totals']['messages'], 38)
            asyncio.run(verify())
