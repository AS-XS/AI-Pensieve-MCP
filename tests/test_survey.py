import asyncio
import json
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from mcp import Client
from mcp.client.stdio import StdioServerParameters, stdio_client

from archive_mcp.db import connect, get_conversation, get_message_context
from archive_mcp.discovery_evaluate import corpus
from archive_mcp.evaluate import seed_corpus
from archive_mcp.mcp_server import create_server
from archive_mcp.read_budget import BudgetExceeded, ReadBudget
from archive_mcp.survey import survey_archive


class SurveyTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.database = self.root / 'test.sqlite'
        self.db = connect(self.database)
        seed_corpus(self.db, corpus())

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_balanced_pages_resume_exactly_and_cover_saved_context(self):
        cursor = None
        got, pages = {}, []
        while True:
            page = survey_archive(self.db, cursor, max_chars=1200)
            self.assertLessEqual(page['characters_returned'], 1200)
            self.assertLessEqual(len(page['records']), 50)
            pages.append(page)
            for record in page['records']:
                key = tuple(record[k] for k in ('provider', 'account', 'conversation_id', 'record_id'))
                self.assertEqual(record['offset'], len(got.get(key, '')))
                got[key] = got.get(key, '') + record['text']
            cursor = page['next_cursor']
            if cursor is None:
                break
            self.assertLess(len(pages), 30)
        self.assertEqual(got, {tuple(r[k] for k in ('provider', 'account', 'conversation_id', 'record_id')): r['text'] for r in corpus()})
        self.assertEqual(pages[0]['records'][0]['provider'], 'chatgpt')
        self.assertEqual((pages[1]['records'][0]['provider'], pages[1]['records'][0]['account']), ('claude', 'work'))
        self.assertTrue(page['complete'])
        self.assertEqual(sum(s['records_completed'] for s in page['sources']), 39)
        self.assertTrue(all(s['status'] == 'complete' for s in page['sources']))

    def test_filters_cursor_retry_and_empty_scope(self):
        first = survey_archive(self.db, providers=['codex'], max_chars=60)
        a = survey_archive(self.db, first['next_cursor'], providers=['codex'], max_chars=60)
        self.assertEqual(a, survey_archive(self.db, first['next_cursor'], providers=['codex'], max_chars=60))
        with self.assertRaises(ValueError):
            survey_archive(self.db, first['next_cursor'], providers=['claude'])
        for cursor in ('bad', 'survey:{}', 'survey:[]'):
            with self.assertRaises(ValueError):
                survey_archive(self.db, cursor)
        self.assertTrue(survey_archive(self.db, providers=['absent'])['complete'])
        empty = survey_archive(self.db, date_from=9999999999)
        self.assertTrue(empty['complete'])
        self.assertEqual(empty['records'], [])

    def test_newest_first_finds_cancellation_across_independent_roots(self):
        graph = get_message_context(self.db, 'codex', 'personal', 'newsletter', 'newsletter-old-plan')
        self.assertEqual(graph['descendants'], [])
        page = get_conversation(self.db, 'codex', 'personal', 'newsletter', limit=1, newest_first=True)
        self.assertEqual(page['messages'][0]['node_source_id'], 'newsletter-cancelled')
        self.assertEqual(page['next_offset'], 1)
        next_page = get_conversation(self.db, 'codex', 'personal', 'newsletter', offset=1, limit=1, newest_first=True)
        self.assertEqual(next_page['messages'][0]['node_source_id'], 'newsletter-old-plan')
        with self.db:
            self.db.execute("UPDATE messages SET created_at=NULL WHERE node_source_id='newsletter-old-plan'")
        page = get_conversation(self.db, 'codex', 'personal', 'newsletter', newest_first=True)
        self.assertEqual(page['undated_messages'], 1)
        self.assertIsNone(page['messages'][-1]['created_at'])

    def test_larger_archive_balances_early_reads_and_reconstructs_all_text(self):
        records = []
        for source in range(8):
            for index in range(300 if source == 0 else 15):
                records.append(dict(record_type='message', provider=f'large-{source}', account='test',
                    conversation_id='session', record_id=str(index), role='user',
                    created_at='2025-01-01T00:00:00Z', title='Synthetic',
                    text=('Unicode 🌱 é\x00 ' * (300 if index == 0 else 30))))
        seed_corpus(self.db, records)
        selected = [f'large-{s}' for s in range(8)]
        page = survey_archive(self.db, providers=selected, max_chars=8000)
        self.assertEqual({r['provider'] for r in page['records']}, set(selected))
        rebuilt = {}
        pages = 0
        while True:
            pages += 1
            for r in page['records']:
                key = (r['provider'], r['record_id'])
                self.assertEqual(r['offset'], len(rebuilt.get(key, '')))
                rebuilt[key] = rebuilt.get(key, '') + r['text']
            if page['next_cursor'] is None:
                break
            page = survey_archive(self.db, page['next_cursor'], providers=selected)
            self.assertLess(pages, 100)
        self.assertEqual(rebuilt, {(r['provider'], r['record_id']): r['text'] for r in records})

    def test_budget_time_and_chars_reject_extra_output(self):
        with patch('archive_mcp.read_budget.time.monotonic', return_value=0):
            budget = ReadBudget(max_calls=2, max_chars=4, max_seconds=10)
            budget.begin()
            budget.finish({'text': '🌱abc'})
            self.assertEqual(budget.characters, 4)
            with self.assertRaises(BudgetExceeded):
                budget.begin()
        with patch('archive_mcp.read_budget.time.monotonic', return_value=11):
            with self.assertRaises(BudgetExceeded):
                budget.check_time()

    def test_mcp_enforces_call_and_output_budgets_without_private_errors(self):
        async def verify():
            async with Client(create_server(self.database, max_calls=2)) as client:
                first = await client.call_tool('survey_archive', {'max_chars': 600})
                self.assertEqual(first.structured_content['read_budget']['calls_remaining'], 1)
                second = await client.call_tool('get_conversation', {'provider': 'codex', 'account': 'personal', 'conversation_id': 'newsletter', 'newest_first': True, 'limit': 1})
                self.assertEqual(second.structured_content['messages'][0]['node_source_id'], 'newsletter-cancelled')
                denied = await client.call_tool('archive_status', {})
                self.assertTrue(denied.is_error)
                self.assertIn('2/2', str(denied.content))
            async with Client(create_server(self.database, max_chars=10, max_calls=3)) as client:
                too_large = await client.call_tool('survey_archive', {'max_chars': 100})
                self.assertTrue(too_large.is_error)
                self.assertNotIn('garden', str(too_large.content))
                small = await client.call_tool('survey_archive', {'max_chars': 10})
                self.assertFalse(small.is_error)
                self.assertEqual(small.structured_content['read_budget']['characters_remaining'], 0)
                denied = await client.call_tool('survey_archive', {'max_chars': 1})
                self.assertTrue(denied.is_error)
            async with Client(create_server(self.database)) as client:
                invalid = await client.call_tool('survey_archive', {'date_from': 'PRIVATE_DATE_MARKER'})
                self.assertTrue(invalid.is_error)
                self.assertNotIn('PRIVATE_DATE_MARKER', str(invalid.content))
        asyncio.run(verify())

    def test_real_stdio_survey_cursor_and_budget(self):
        params = StdioServerParameters(command=sys.executable,
            args=['-m', 'archive_mcp.mcp_server', str(self.database), '--max-read-calls', '2'],
            env={'PYTHONPATH': str(Path(__file__).resolve().parents[1] / 'src')}, cwd=self.root)
        async def verify():
            async with Client(stdio_client(params), read_timeout_seconds=10) as client:
                first = await client.call_tool('survey_archive', {'max_chars': 600})
                cursor = first.structured_content['next_cursor']
                second = await client.call_tool('survey_archive', {'cursor': cursor, 'max_chars': 600})
                self.assertFalse(second.is_error)
                self.assertEqual(second.structured_content['pages_read'], 2)
                denied = await client.call_tool('survey_archive', {'cursor': second.structured_content['next_cursor']})
                self.assertTrue(denied.is_error)
        asyncio.run(verify())
