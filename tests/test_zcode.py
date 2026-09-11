import asyncio
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from mcp import Client

from archive_mcp.auto_import import import_all, scan_summary, sqlite_format
from archive_mcp.batches import run_batch
from archive_mcp.cli import parser
from archive_mcp.db import connect, integrity_status, search
from archive_mcp.mcp_server import create_server
from archive_mcp.zcode import import_file


def create_source(path):
    """Invented content with the relevant observed ZCode SQLite columns."""
    with closing(sqlite3.connect(path)) as db, db:
        db.executescript("""
            CREATE TABLE session(id TEXT PRIMARY KEY, title TEXT, time_created INTEGER,
                time_updated INTEGER, title_source TEXT);
            CREATE TABLE message(id TEXT PRIMARY KEY, session_id TEXT, data TEXT,
                sequence INTEGER, time_created INTEGER);
            CREATE TABLE part(id TEXT PRIMARY KEY, message_id TEXT, session_id TEXT,
                data TEXT, sequence INTEGER, time_created INTEGER);
            CREATE TABLE session_input(admitted_sequence INTEGER, promoted_message_id TEXT);
            CREATE TABLE schema_migration(app_version TEXT, time_applied INTEGER);
            INSERT INTO session VALUES('session-1','Synthetic research',1756684800000,
                1756684809000,'first_input');
            INSERT INTO session VALUES('empty','Empty',1756684800000,1756684800000,'default');
        """)
        specs = [
            ('user', None, 'user', 'Archive SQLite research', 'text'),
            ('hidden', 'user', 'assistant', 'hiddenreasoningmarker', 'reasoning'),
            ('left', 'hidden', 'assistant', 'First SQLite answer', 'text'),
            ('right', 'user', 'assistant', 'Alternative SQLite answer', 'text'),
            ('reminder', 'right', 'user', 'hiddenremindermarker', 'text'),
            ('timeline', 'right', 'assistant', 'hiddentimelinemarker', 'text'),
        ]
        for i, (key, parent, role, text, kind) in enumerate(specs):
            data = {'role': role, 'semantics': {
                'origin': 'real_user' if role == 'user' else 'agent_runtime',
                'kind': 'user_prompt' if role == 'user' else 'assistant_response',
                'uiVisibility': 'visible',
            }}
            if parent is not None:
                data['parentID'] = parent
            if key == 'reminder':
                data['synthetic'] = True
            if key == 'timeline':
                data['semantics']['kind'] = 'timeline_event'
            db.execute('INSERT INTO message VALUES(?,?,?,?,?)',
                       (key, 'session-1', json.dumps(data), i, 1756684800000 + i * 1000))
            db.execute('INSERT INTO part VALUES(?,?,?,?,?,?)',
                       ('part-' + key, key, 'session-1',
                        json.dumps({'type': kind, 'text': text}), i, 1756684800000))
        for i, extra in enumerate([
            {'type': 'text', 'text': 'hiddeninjectedmarker', 'synthetic': True},
            {'type': 'text', 'text': 'hiddenignoredmarker', 'ignored': True},
            {'type': 'tool', 'text': 'hiddentoolmarker'},
            {'type': 'file', 'text': 'hiddenattachmentmarker'},
            {'type': 'text', 'text': 'Second paragraph 🌱'},
        ]):
            db.execute('INSERT INTO part VALUES(?,?,?,?,?,?)',
                       (f'extra-{i}', 'left', 'session-1', json.dumps(extra), i + 10, 1756684800000))


class ZCodeImportTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / 'db.sqlite'
        create_source(self.source)
        self.database = self.root / 'archive.sqlite'
        self.db = connect(self.database)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_visible_dialogue_branches_provenance_and_repeat_import(self):
        original = self.source.read_bytes()
        expected = {'conversations': 1, 'nodes': 3}
        self.assertEqual(import_file(self.db, self.source, 'personal'), expected)
        self.assertEqual(import_file(self.db, self.source, 'personal'), expected)
        rows = self.db.execute('SELECT node_source_id, parent_source_id FROM messages ORDER BY id')
        self.assertEqual([tuple(r) for r in rows], [('user', None), ('left', 'user'), ('right', 'user')])
        matches = search(self.db, 'SQLite')
        self.assertEqual(len(matches), 3)
        self.assertTrue(all(r['provider'] == 'zcode' and r['account'] == 'personal' for r in matches))
        row = self.db.execute('SELECT source_id, source_file, created_at FROM conversations').fetchone()
        self.assertEqual(tuple(row), ('session-1', str(self.source), 1756684800))
        self.assertEqual(search(self.db, 'hidden*'), [])
        body = self.db.execute("SELECT text FROM messages WHERE node_source_id='left'").fetchone()[0]
        self.assertEqual(body, 'First SQLite answer\n\nSecond paragraph 🌱')
        self.assertTrue(integrity_status(self.db)['ok'])
        self.assertEqual(self.source.read_bytes(), original)
        self.assertFalse(Path(str(self.source) + '-shm').exists())

    def test_detection_batch_and_explicit_cli(self):
        self.assertEqual(sqlite_format(self.source), 'zcode')
        selected = self.root / 'chosen folder' / 'nested'
        selected.mkdir(parents=True)
        copied = selected / 'custom-name.sqlite'
        copied.write_bytes(self.source.read_bytes())
        (selected / 'unsupported.json').write_text('{"unknown": true}')
        self.assertEqual(scan_summary([selected.parent]), {
            'candidate_files': 2, 'files': 1, 'formats': {'zcode': 1}, 'ignored_files': 1,
        })
        result = import_all(self.db, [selected.parent], 'chosen')
        self.assertEqual(result['formats'], {'zcode': 1})
        self.assertEqual(result['nodes'], 3)
        args = parser().parse_args(['import-zcode', str(self.database), str(self.source)])
        self.assertEqual(args.files, [str(self.source)])
        with closing(sqlite3.connect(self.source)) as native, native:
            native.execute('DROP TABLE session_input')
        self.assertIsNone(sqlite_format(self.source))
        with self.assertRaises(ValueError):
            import_file(self.db, self.source)

    def test_empty_source_warns_and_preserves_previous_records(self):
        import_file(self.db, self.source)
        with closing(sqlite3.connect(self.source)) as native, native:
            native.execute('DELETE FROM part')
        result = run_batch(self.db, [('zcode', self.source, import_file)], 'default', 'explicit')
        self.assertEqual(result['warnings'], {'no_indexable_records': 1})
        self.assertEqual(result['conversations'], 0)
        self.assertEqual(self.db.execute('SELECT count(*) FROM messages').fetchone()[0], 3)

    def test_malformed_later_session_is_atomic_and_error_report_is_private(self):
        with closing(sqlite3.connect(self.source)) as native, native:
            native.execute("INSERT INTO message VALUES('broken','empty',?,0,1756684800000)",
                           ('PRIVATE_MARKER not JSON',))
        with self.assertRaises(json.JSONDecodeError):
            run_batch(self.db, [('zcode', self.source, import_file)], 'default', 'explicit')
        self.assertEqual(self.db.execute('SELECT count(*) FROM conversations').fetchone()[0], 0)
        warning = self.db.execute('SELECT code, detail FROM import_warnings').fetchone()
        self.assertEqual(tuple(warning), ('import_failed', 'JSONDecodeError'))

    def test_wal_is_not_silently_ignored(self):
        with closing(sqlite3.connect(self.source)) as native:
            native.execute('PRAGMA journal_mode=WAL')
            native.execute("UPDATE session SET title='Uncheckpointed'")
            native.commit()
            with self.assertRaisesRegex(ValueError, 'Close ZCode'):
                import_file(self.db, self.source)

    def test_mcp_can_search_and_fetch_without_source_path_disclosure(self):
        import_file(self.db, self.source, 'personal')
        original = self.source.read_bytes()
        async def verify():
            async with Client(create_server(self.database, self.root / 'mcp.jsonl')) as client:
                found = await client.call_tool('search_history', {'query': 'SQLite', 'providers': ['zcode']})
                self.assertFalse(found.is_error)
                self.assertEqual(len(found.structured_content['result']), 3)
                page = await client.call_tool('get_conversation', {
                    'provider': 'zcode', 'account': 'personal', 'conversation_id': 'session-1',
                })
                self.assertFalse(page.is_error)
                self.assertEqual(len(page.structured_content['messages']), 3)
                self.assertNotIn('source_file', page.structured_content['conversation'])
                self.assertNotIn(str(self.source), json.dumps(page.structured_content))
        asyncio.run(verify())
        self.assertEqual(self.source.read_bytes(), original)
