import io
import sys
from types import SimpleNamespace
from contextlib import redirect_stderr
import json
from pathlib import Path
import shutil
import tempfile
import threading
import unittest
from unittest.mock import patch
from contextlib import closing

from archive_mcp.db import connect, integrity_status
from archive_mcp.gui import FORMATS, GuiBridge, GuiService, main, page_html
from archive_mcp.auto_import import IMPORTERS

FIXTURES = Path(__file__).parents[1] / 'fixtures'


class GuiTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.sources = self.root/'sources'
        self.sources.mkdir()
        self.service = GuiService(self.root/'archive.sqlite')
        self.bridge = GuiBridge(self.service, lambda folder: None)

    def tearDown(self):
        self.temp.cleanup()

    def copy(self, name, destination=None):
        path = self.sources/(destination or name)
        shutil.copyfile(FIXTURES/name, path)
        return path

    def test_preview_selection_does_not_import_or_mislabel_formats(self):
        self.copy('chatgpt.json'); self.copy('claude.json')
        (self.sources/'unknown.json').write_text('{"unrecognized": true}')
        preview = self.service.preview(self.sources, 'claude')
        self.assertEqual((preview['files'], preview['unrecognized'], preview['other_formats']), (1, 1, 1))
        self.assertEqual(preview['formats'], {'claude': 1})
        self.assertEqual(self.service.status()['totals']['conversations'], 0)
        self.assertEqual(set(FORMATS)-{'auto'}, set(IMPORTERS))
        self.assertEqual(self.bridge.choose()['data'], None)
        self.assertFalse(self.bridge.preview(str(self.root/'missing'), 'auto')['ok'])

    def test_import_repeat_filters_and_source_immutability(self):
        self.copy('chatgpt.json'); self.copy('claude.json'); self.copy('memories.json')
        originals = {p: p.read_bytes() for p in self.sources.iterdir()}
        first = self.service.import_sources(self.sources, account='personal')
        second = self.service.import_sources(self.sources, account='personal')
        self.assertEqual((first['completed'],first['total'],first['error']), (3,3,None))
        self.assertEqual(first['changes']['nodes']['new'], 6)
        self.assertEqual(second['changes']['nodes']['unchanged'], 6)
        self.assertEqual(second['changes']['nodes']['new'], 0)
        groups = self.service.search('archive', 'claude', 'personal')['groups']
        self.assertEqual(len(groups),1)
        self.assertEqual((groups[0]['provider'],groups[0]['account']), ('claude','personal'))
        self.assertEqual(self.service.search('archive', 'claude', 'work')['groups'], [])
        self.assertEqual(self.service.progress(), {'running':False,'completed':3,'total':3})
        self.assertEqual({p: p.read_bytes() for p in originals}, originals)

    def test_partial_failure_returns_committed_counts_and_private_error(self):
        self.copy('chatgpt.json','a-good.json')
        bad = json.loads((FIXTURES/'claude.json').read_text())
        bad[0]['chat_messages'][0].pop('uuid')
        (self.sources/'z-bad.json').write_text(json.dumps(bad))
        result = self.service.import_sources(self.sources)
        self.assertEqual((result['completed'],result['total']), (1,2))
        self.assertEqual(result['changes']['conversations']['new'],1)
        self.assertIn('KeyError',result['error'])
        self.assertNotIn('chat_messages',result['error'])
        with closing(connect(self.service.database, read_only=True)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM conversations').fetchone()[0],1)
            self.assertEqual([r[0] for r in db.execute('SELECT status FROM import_batches ORDER BY id')], ['completed','failed'])
        self.assertFalse(self.service.progress()['running'])

    def test_conversation_and_saved_context_continuations_are_exact_and_read_only(self):
        path=self.copy('chatgpt.json')
        data=json.loads(path.read_text())
        hostile='<img src="https://example.invalid/x" onerror="alert(1)">'
        body=hostile+'🌱漢字'*2800+'END_OF_MESSAGE'
        data[0]['mapping']['user-1']['message']['content']['parts']=[body]
        # Enough visible messages to exercise conversation pagination as well.
        for n in range(25):
            data[0]['mapping'][f'extra-{n}']={'parent':'user-1','message':{
                'id':f'id-{n}','author':{'role':'assistant'},'content':{'parts':[f'Extra {n}']}}}
        path.write_text(json.dumps(data))
        memory=self.copy('memories.json');saved=json.loads(memory.read_text())
        saved['memories'][0]['text']=body;memory.write_text(json.dumps(saved))
        self.service.import_sources(self.sources)
        before=self.service.database.read_bytes()
        first=self.service.conversation('chatgpt','default','conversation-1')
        self.assertEqual(len(first['messages']),20)
        self.assertEqual(first['next_offset'],20)
        second=self.service.conversation('chatgpt','default','conversation-1',20)
        self.assertEqual(len(second['messages']),8)
        self.assertIsNone(second['next_offset'])
        text=first['messages'][0]['text'];offset=4000
        while offset is not None:
            page=self.service.message('chatgpt','default','conversation-1','user-1',offset)
            text+=page['text'];offset=page['next_offset']
        self.assertEqual(text,body)
        text='';offset=0
        while offset is not None:
            page=self.service.memory(saved['provider'],'default',saved['memories'][0]['id'],offset)
            text+=page['text'];offset=page['next_offset']
        self.assertEqual(text,body)
        self.assertEqual(self.service.database.read_bytes(),before)
        with closing(connect(self.service.database)) as db:
            self.assertTrue(integrity_status(db)['ok'])

    def test_gui_bridge_errors_never_forward_parser_text(self):
        with patch.object(self.service,'search',side_effect=ValueError('private-content-marker')):
            result=self.bridge.search('x','','')
        self.assertFalse(result['ok'])
        self.assertNotIn('private-content-marker',str(result))
        self.assertFalse(self.bridge.search('"','','')['ok'])
        self.assertTrue(self.bridge.status()['ok'])

    def test_concurrent_import_is_rejected_and_progress_is_visible(self):
        self.copy('chatgpt.json')
        entered=threading.Event();release=threading.Event();results=[]
        from archive_mcp.gui import run_batch as original
        def paused(*args,**kwargs):
            entered.set()
            if not release.wait(5):
                raise RuntimeError('test timeout')
            return original(*args,**kwargs)
        with patch('archive_mcp.gui.run_batch',side_effect=paused):
            worker=threading.Thread(target=lambda:results.append(self.service.import_sources(self.sources)))
            worker.start()
            try:
                self.assertTrue(entered.wait(5))
                self.assertEqual(self.service.progress(), {'running':True,'completed':0,'total':1})
                with self.assertRaises(ValueError):
                    self.service.import_sources(self.sources)
            finally:
                release.set();worker.join(5)
        self.assertFalse(worker.is_alive())
        self.assertEqual(results[0]['completed'],1)

    def test_startup_error_is_actionable_without_private_path_or_traceback(self):
        invalid=self.root/'private-path-marker.sqlite'
        invalid.write_text('not a SQLite archive')
        output=io.StringIO()
        with patch.dict(sys.modules, {'webview':SimpleNamespace()}), redirect_stderr(output):
            with self.assertRaises(SystemExit) as stopped:
                main(['--database',str(invalid)])
        self.assertEqual(stopped.exception.code,1)
        self.assertIn('Check --database',output.getvalue())
        self.assertNotIn('private-path-marker',output.getvalue())
        self.assertNotIn('Traceback',output.getvalue())

    def test_packaged_page_is_self_contained_and_uses_text_rendering(self):
        page=page_html()
        self.assertNotIn('BUNDLED_',page)
        self.assertIn("connect-src 'none'",page)
        self.assertNotIn('<script src=',page)
        self.assertNotIn('innerHTML',page)
        self.assertIn('node.textContent = text',page)
        self.assertIn('pywebviewready',page)

    def test_shelf_browse_separates_sources_and_paginates_stably(self):
        self.copy('chatgpt.json'); self.copy('memories.json')
        self.service.import_sources(self.sources, account='personal')
        self.service.import_sources(self.sources, account='work')
        with closing(connect(self.service.database)) as db:
            account_id=db.execute("SELECT id FROM source_accounts WHERE provider='chatgpt' AND label='personal'").fetchone()[0]
            for n in range(35):
                db.execute('INSERT INTO conversations(account_id,source_id,source_file,title,created_at) VALUES (?,?,?,?,?)',
                           (account_id,f'shelf-{n:02d}','synthetic','Same title',100))
            db.commit()
        before=self.service.database.read_bytes()
        first=self.service.library('chatgpt','personal')
        second=self.service.library('chatgpt','personal',first['next_offset'])
        self.assertEqual((len(first['groups']),len(second['groups'])),(30,6))
        self.assertIsNone(second['next_offset'])
        combined=first['groups']+second['groups']
        self.assertEqual(len({g['conversation_id'] for g in combined}),36)
        self.assertTrue(all(g['provider']=='chatgpt' and g['account']=='personal' for g in combined))
        self.assertEqual(len(self.bridge.library('chatgpt','work')['data']['groups']),1)
        saved=[g for g in self.service.library('', 'work')['groups'] if g['group_type']=='memory']
        self.assertEqual(len(saved),1)
        self.assertTrue(self.service.memory(saved[0]['provider'],'work',saved[0]['memory_id'])['text'])
        self.assertEqual(self.service.database.read_bytes(),before)

    def test_scene_assets_and_initial_door_survive_packaging(self):
        page=page_html()
        self.assertIn('<body data-scene="door">',page)
        self.assertRegex(page, r'id="chamber"\s+aria-label="The Pensieve chamber"\s+inert')
        self.assertIn('id="open-door"',page)
        self.assertEqual(page.count('data:image/png;base64,'),4)
        self.assertEqual(page.count('data:image/svg+xml;base64,'),10)
        for token in ('__CHAMBER__','__DOOR__','__OVERHEAD__','BUNDLED_'):
            self.assertNotIn(token,page)
        self.assertIn('prefers-reduced-motion',page)

    def test_one_click_local_discovery_uses_only_known_roots_and_keeps_sources(self):
        import os
        from test_zcode import create_source
        home=self.root/'synthetic-home'
        paths={
            home/'.codex/sessions/2026/09/session.jsonl':'codex_session.jsonl',
            home/'.claude/projects/project/session.jsonl':'claude_code.jsonl',
            home/'.qwen/projects/project/chats/session.jsonl':'qwen_code.jsonl',
        }
        for path, fixture in paths.items():
            path.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(FIXTURES/fixture,path)
        zcode=home/'.zcode/cli/db/db.sqlite';zcode.parent.mkdir(parents=True)
        create_source(zcode)
        unrelated=home/'Documents/private.json';unrelated.parent.mkdir()
        unrelated.write_text('Do not inspect arbitrary files')
        originals={p:p.read_bytes() for p in [*paths,zcode,unrelated]}
        from archive_mcp.sync import local_sources as original_sources
        def known_roots(*roots):
            self.assertEqual(roots,(home/'.codex/sessions',home/'.claude/projects',home/'.gemini/antigravity/conversations',home/'.qwen/projects'))
            return original_sources(*roots)
        with patch('archive_mcp.gui.Path.home',return_value=home), patch.dict(os.environ,{'CODEX_HOME':str(home/'.codex')}), patch('archive_mcp.gui.local_sources',side_effect=known_roots):
            first=self.bridge.import_local('personal')['data']
            again=self.service.import_local('personal')
        self.assertEqual(first['completed'],4)
        self.assertEqual(first['formats'],{'codex':1,'claude-code':1,'qwen-code':1,'zcode':1})
        self.assertEqual(again['changes']['nodes']['new'],0)
        self.assertGreater(again['changes']['nodes']['unchanged'],0)
        self.assertEqual({p:p.read_bytes() for p in originals},originals)
        self.assertEqual(self.service.search('private')['groups'],[])

    def test_one_click_missing_native_roots_is_an_honest_empty_result(self):
        import os
        home=self.root/'no-apps'
        with patch('archive_mcp.gui.Path.home',return_value=home), patch.dict(os.environ,{'CODEX_HOME':str(home/'.codex')}):
            result=self.service.import_local()
        self.assertEqual((result['completed'],result['total'],result['error']),(0,0,None))
        self.assertEqual(result['formats'],{})
        self.assertFalse(self.service.progress()['running'])
