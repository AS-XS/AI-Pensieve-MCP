import copy
import json
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from archive_mcp.chatgpt import import_file as import_chatgpt
from archive_mcp.claude import import_file as import_claude
from archive_mcp.codex_local import import_file as import_codex
from archive_mcp.db import connect, search


FIXTURES = Path(__file__).parents[1] / 'fixtures'


class ReimportExportsTest(unittest.TestCase):
    def test_overlapping_monthly_exports_use_ids_not_titles_or_file_paths(self):
        for provider, importer in [('chatgpt', import_chatgpt), ('claude', import_claude)]:
            with self.subTest(provider=provider), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                old = json.loads((FIXTURES / f'{provider}.json').read_text())
                new = copy.deepcopy(old)
                conversation = new[0]
                id_key, title_key = ('id', 'title') if provider == 'chatgpt' else ('uuid', 'name')
                conversation[title_key] = 'Renamed ongoing discussion'
                if provider == 'chatgpt':
                    node = copy.deepcopy(conversation['mapping']['user-1'])
                    node.update(id='monthly-new', parent='assistant-local')
                    node['message']['id'] = 'monthly-message'
                    node['message']['content']['parts'] = ['Newmonthlyevidence in this existing thread.']
                    conversation['mapping']['monthly-new'] = node
                else:
                    node = copy.deepcopy(conversation['chat_messages'][0])
                    node.update(uuid='monthly-new', parent_message_uuid='claude-assistant-1',
                                text='Newmonthlyevidence in this existing thread.')
                    conversation['chat_messages'].append(node)
                old_path, new_path = root/'old-export.json', root/'new-export.json'
                old_path.write_text(json.dumps(old)); new_path.write_text(json.dumps(new))
                originals = (old_path.read_bytes(), new_path.read_bytes())
                with closing(connect(root/'archive.sqlite')) as db:
                    importer(db, old_path, 'personal')
                    original_id = db.execute('SELECT id FROM conversations').fetchone()[0]
                    original_count = db.execute('SELECT count(*) FROM messages').fetchone()[0]
                    importer(db, new_path, 'personal'); importer(db, new_path, 'personal')
                    row = db.execute('SELECT id, title FROM conversations').fetchone()
                    self.assertEqual(tuple(row), (original_id, 'Renamed ongoing discussion'))
                    self.assertEqual(db.execute('SELECT count(*) FROM messages').fetchone()[0], original_count + 1)
                    self.assertEqual(len(search(db, 'Newmonthlyevidence')), 1)
                    self.assertEqual(db.execute("SELECT parent_source_id FROM messages WHERE node_source_id='monthly-new'").fetchone()[0], node['parent'] if provider == 'chatgpt' else node['parent_message_uuid'])
                    # Different original IDs with the same title remain separate.
                    other = copy.deepcopy(conversation); other[id_key] = 'different-thread'
                    distinct = root/'same-title.json'; distinct.write_text(json.dumps([other]))
                    importer(db, distinct, 'personal')
                    self.assertEqual(db.execute('SELECT count(*) FROM conversations').fetchone()[0], 2)
                    # Identical IDs under another account are not duplicate identities.
                    importer(db, new_path, 'work')
                    self.assertEqual(db.execute('SELECT count(*) FROM conversations').fetchone()[0], 3)
                self.assertEqual((old_path.read_bytes(), new_path.read_bytes()), originals)

    def test_appended_native_codex_session_does_not_duplicate_earlier_dialogue(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root/'session.jsonl'
            initial = (FIXTURES/'codex_session.jsonl').read_text()
            source.write_text(initial)
            with closing(connect(root/'archive.sqlite')) as db:
                importer_result = import_codex(db, source, 'personal')
                row = dict(timestamp='2025-01-03T12:00:00Z', type='response_item', payload=dict(
                    type='message', role='user', content=[dict(type='input_text', text='Appendedmonthlyevidence')]))
                updated = initial.rstrip() + '\n' + json.dumps(row) + '\n'
                source.write_text(updated)
                import_codex(db, source, 'personal'); import_codex(db, source, 'personal')
                self.assertEqual(db.execute('SELECT count(*) FROM conversations').fetchone()[0], 1)
                self.assertEqual(db.execute('SELECT count(*) FROM messages').fetchone()[0], importer_result['nodes'] + 1)
                self.assertEqual(len(search(db, 'Appendedmonthlyevidence')), 1)
            self.assertEqual(source.read_text(), updated)
