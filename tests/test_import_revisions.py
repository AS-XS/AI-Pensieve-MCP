import copy
import json
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from archive_mcp.batches import import_report, run_batch
from archive_mcp.chatgpt import import_file as import_chatgpt
from archive_mcp.claude import import_file as import_claude
from archive_mcp.codex_local import import_file as import_codex
from archive_mcp.db import connect, integrity_status, search
from archive_mcp.gemini import import_file as import_gemini
from archive_mcp.memories import import_file as import_memories
from import_expectations import expected_result

FIXTURES = Path(__file__).parents[1] / 'fixtures'


class ImportRevisionTest(unittest.TestCase):
    def test_newer_then_older_preserves_edits_and_adds_unseen_old_branches(self):
        for provider, importer in [('chatgpt', import_chatgpt), ('claude', import_claude)]:
            with self.subTest(provider=provider), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                old = json.loads((FIXTURES / f'{provider}.json').read_text())
                new = copy.deepcopy(old)
                if provider == 'chatgpt':
                    new[0]['update_time'] = old[0]['update_time'] + 100
                    new[0]['title'] = 'Newrevisiontitle'
                    new[0]['mapping']['user-1']['message']['content']['parts'] = ['Newrevisiontext']
                    extra = copy.deepcopy(old[0]['mapping']['user-1'])
                    extra['message']['id'] = 'recovered-message'
                    extra['message']['content']['parts'] = ['Recoveredbranch']
                    old[0]['mapping']['recovered-node'] = extra
                    initial_nodes = 4
                else:
                    new[0]['updated_at'] = '2026-01-01T00:00:00Z'
                    new[0]['name'] = 'Newrevisiontitle'
                    new[0]['chat_messages'][0]['text'] = 'Newrevisiontext'
                    extra = copy.deepcopy(old[0]['chat_messages'][0])
                    extra.update(uuid='recovered-node', text='Recoveredbranch')
                    old[0]['chat_messages'].append(extra)
                    initial_nodes = 2
                newer, older = root/'new.json', root/'old.json'
                newer.write_text(json.dumps(new)); older.write_text(json.dumps(old))
                original_bytes = (newer.read_bytes(), older.read_bytes())
                with closing(connect(root/'db.sqlite')) as db:
                    first = importer(db, newer)
                    self.assertEqual(first, expected_result(dict(conversations=1, nodes=initial_nodes)))
                    protected = importer(db, older)['changes']
                    self.assertEqual(protected['conversations']['protected'], 1)
                    self.assertEqual(protected['nodes']['protected'], 1)
                    self.assertEqual(protected['nodes']['new'], 1)
                    self.assertEqual(protected['nodes']['unchanged'], initial_nodes-1)
                    self.assertEqual(tuple(db.execute('SELECT title, source_file FROM conversations').fetchone()),
                                     ('Newrevisiontitle', str(newer)))
                    self.assertEqual(len(search(db, 'Newrevisiontext')), 1)
                    self.assertEqual(len(search(db, 'Recoveredbranch')), 1)
                    before = db.total_changes
                    repeat = importer(db, newer)
                    self.assertEqual(repeat, expected_result(dict(conversations=1, nodes=initial_nodes), 'unchanged'))
                    self.assertEqual(db.total_changes, before)
                    self.assertTrue(integrity_status(db)['ok'])
                self.assertEqual((newer.read_bytes(), older.read_bytes()), original_bytes)

    def test_equal_and_missing_revision_policy_and_content_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root/'export.json'
            data = json.loads((FIXTURES/'chatgpt.json').read_text())
            data[0]['update_time'] = None
            source.write_text(json.dumps(data))
            with closing(connect(root/'db.sqlite')) as db:
                import_chatgpt(db, source)
                # Unknown chronology: changed content is accepted, without inventing an edit date.
                data[0]['title'] = 'Undatedtitle'
                source.write_text(json.dumps(data))
                self.assertEqual(import_chatgpt(db, source)['changes']['conversations']['updated'], 1)
                data[0]['update_time'] = 2000000000
                data[0]['mapping']['user-1']['message']['content']['parts'] = ['Updatedtoken']
                source.write_text(json.dumps(data))
                changed = import_chatgpt(db, source)['changes']
                self.assertEqual(changed['conversations']['updated'], 1)
                self.assertEqual(changed['nodes']['updated'], 1)
                self.assertEqual(changed['nodes']['unchanged'], 3)
                data[0]['title'] = 'Equalrevisiontitle'
                source.write_text(json.dumps(data))
                self.assertEqual(import_chatgpt(db, source)['changes']['conversations']['updated'], 1)
                data[0]['update_time'] = None
                data[0]['title'] = 'Missingrevisiontitle'
                data[0]['mapping']['user-1']['message']['content']['parts'] = ['Rejectedtoken']
                source.write_text(json.dumps(data))
                blocked = import_chatgpt(db, source)['changes']
                self.assertEqual(blocked['conversations']['protected'], 1)
                self.assertEqual(blocked['nodes']['protected'], 1)
                self.assertEqual(search(db, 'Rejectedtoken'), [])
                self.assertEqual(len(search(db, 'Updatedtoken')), 1)
                self.assertEqual(db.execute('SELECT title FROM conversations').fetchone()[0], 'Equalrevisiontitle')

    def test_codex_old_snapshot_cannot_remove_new_tail_and_pruning_is_counted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); older = root/'old.jsonl'; newer = root/'new.jsonl'
            initial = (FIXTURES/'codex_session.jsonl').read_text()
            older.write_text(initial)
            tail = dict(timestamp='2025-01-03T12:00:00Z', type='response_item', payload=dict(
                type='message', role='user', content=[dict(type='input_text', text='Retainedtail')]))
            newer.write_text(initial.rstrip()+'\n'+json.dumps(tail)+'\n')
            with closing(connect(root/'db.sqlite')) as db:
                import_codex(db, older)
                updated = import_codex(db, newer)['changes']
                self.assertEqual(updated['nodes']['new'], 1)
                self.assertEqual(updated['nodes']['unchanged'], 2)
                rejected = import_codex(db, older)['changes']
                self.assertEqual(rejected['conversations']['protected'], 1)
                self.assertEqual(rejected['nodes']['removed'], 0)
                self.assertEqual(len(search(db, 'Retainedtail')), 1)
                key = db.execute('SELECT id FROM conversations').fetchone()[0]
                with db:
                    db.execute("INSERT INTO messages(conversation_id,node_source_id,role,text) VALUES (?, 'excluded', 'user', 'Excludedtoken')", (key,))
                refreshed = import_codex(db, newer)['changes']
                self.assertEqual(refreshed['nodes']['unchanged'], 3)
                self.assertEqual(refreshed['nodes']['removed'], 1)
                self.assertEqual(search(db, 'Excludedtoken'), [])
                self.assertTrue(integrity_status(db)['ok'])

    def test_gemini_snapshot_replacement_counts_removals_and_preserves_other_accounts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root/'activity.html'
            source.write_text((FIXTURES/'gemini.html').read_text())
            with closing(connect(root/'db.sqlite')) as db:
                import_gemini(db, source, 'personal')
                import_gemini(db, source, 'work')
                before = db.total_changes
                repeated = import_gemini(db, source, 'personal')
                self.assertEqual(repeated, expected_result(dict(conversations=2, nodes=5), 'unchanged'))
                self.assertEqual(db.total_changes, before)
                source.write_text('<html></html>')
                removed = import_gemini(db, source, 'personal')['changes']
                self.assertEqual(removed['conversations']['removed'], 2)
                self.assertEqual(removed['nodes']['removed'], 5)
                self.assertEqual(db.execute('SELECT count(*) FROM messages').fetchone()[0], 5)
                self.assertTrue(integrity_status(db)['ok'])

    def test_saved_context_and_path_only_changes_are_counted_honestly(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root/'memory.json'; moved = root/'moved.json'
            data = json.loads((FIXTURES/'memories.json').read_text())
            source.write_text(json.dumps(data)); moved.write_text(json.dumps(data))
            with closing(connect(root/'db.sqlite')) as db:
                import_memories(db, source)
                self.assertEqual(import_memories(db, moved), expected_result(dict(memories=1), 'unchanged'))
                self.assertEqual(db.execute('SELECT source_file FROM memories').fetchone()[0], str(moved))
                data['memories'][0]['text'] = 'Replacedsavedcontext'
                moved.write_text(json.dumps(data))
                self.assertEqual(import_memories(db, moved)['changes']['memories']['updated'], 1)
                before = db.total_changes
                self.assertEqual(import_memories(db, moved), expected_result(dict(memories=1), 'unchanged'))
                self.assertEqual(db.total_changes, before)

    def test_duplicate_ids_are_net_counts_and_batch_counts_sum_committed_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root/'export.json'
            data = json.loads((FIXTURES/'chatgpt.json').read_text())
            second = copy.deepcopy(data[0]); second['title'] = 'Finaltitle'
            source.write_text(json.dumps([data[0], second]))
            with closing(connect(root/'db.sqlite')) as db:
                first = import_chatgpt(db, source)
                self.assertEqual(first['conversations'], 2)
                self.assertEqual(first['nodes'], 8)
                self.assertEqual(first['changes'], expected_result(dict(conversations=1, nodes=4))['changes'])
                self.assertEqual(db.execute('SELECT title FROM conversations').fetchone()[0], 'Finaltitle')
                result = run_batch(db, [('chatgpt', source, import_chatgpt)]*2, 'default', 'test')
                self.assertEqual(result['changes'], expected_result(dict(conversations=2, nodes=8), 'unchanged')['changes'])

    def test_failed_file_rolls_back_content_and_next_import_has_fresh_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); good = root/'good.json'; bad = root/'bad.json'
            data = json.loads((FIXTURES/'chatgpt.json').read_text())
            good.write_text(json.dumps(data))
            changed = copy.deepcopy(data[0]); changed['title'] = 'Rolledbacktitle'
            changed['update_time'] += 100
            bad.write_text(json.dumps([changed, {'mapping': {}}]))
            with closing(connect(root/'db.sqlite')) as db:
                with self.assertRaises(KeyError):
                    run_batch(db, [('chatgpt', good, import_chatgpt), ('chatgpt', bad, import_chatgpt)], 'default', 'test')
                report = import_report(db)[0]
                self.assertEqual((report['status'], report['imported_files']), ('failed', 1))
                self.assertEqual(db.execute('SELECT title FROM conversations').fetchone()[0], data[0]['title'])
                self.assertEqual(import_chatgpt(db, good), expected_result(dict(conversations=1, nodes=4), 'unchanged'))
                self.assertTrue(integrity_status(db)['ok'])
