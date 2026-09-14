"""Optional desktop GUI. Uses a native bridge, never an HTTP service."""

import argparse
import base64
import json
from collections import Counter
from contextlib import closing
from functools import wraps
from importlib.resources import files
from pathlib import Path
import sqlite3
import threading

from .auto_import import classify, IMPORTERS
from .batches import run_batch
from .sync import default_roots, local_sources
from .db import (
    archive_status, connect, get_conversation, get_message, initialize,
    search_conversations,
)

FORMATS = {
    'auto': 'Auto-detect all supported formats',
    'chatgpt': 'ChatGPT · export', 'claude': 'Claude · conversations',
    'claude-context': 'Claude · projects & saved context',
    'deepseek': 'DeepSeek · export', 'grok': 'Grok · export',
    'gemini': 'Gemini · activity HTML (replaces activity)',
    'notebooklm': 'NotebookLM · metadata only',
    'memories': 'Generic saved context',
    'codex': 'Codex · local session', 'claude-code': 'Claude Code · local session',
    'qwen-code': 'Qwen Code · session/export', 'opencode': 'OpenCode · JSON export',
    'antigravity': 'Antigravity · observed local store',
    'zcode': 'ZCode · closed SQLite store',
}


class GuiService:
    """Testable local operations; connections belong to the calling thread."""

    def __init__(self, database):
        self.database = Path(database).expanduser().resolve()
        self.database.parent.mkdir(parents=True, exist_ok=True)
        with closing(connect(self.database)) as db:
            initialize(db)
        self._import_lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._progress = {'running': False, 'completed': 0, 'total': 0}

    def status(self):
        with closing(connect(self.database, read_only=True)) as db:
            return {'database': str(self.database), 'formats': FORMATS, **archive_status(db)}

    def preview(self, path, source_format='auto'):
        selected, ignored, excluded = self._selection(path, source_format)
        return {
            'files': len(selected), 'formats': dict(Counter(kind for kind, _ in selected)),
            'unrecognized': len(ignored), 'other_formats': excluded,
            'note': 'Only supported JSON, JSONL, HTML and native-store candidates are inspected. Extract ZIPs first.',
        }

    def _selection(self, path, source_format):
        if not str(path).strip():
            raise ValueError('Choose a source file or folder first.')
        if source_format not in FORMATS:
            raise ValueError('Select a supported format or auto-detect.')
        found, ignored = classify([Path(path).expanduser()])
        selected = [(kind, source) for kind, source in found if source_format in ('auto', kind)]
        return selected, ignored, len(found) - len(selected)

    def progress(self):
        with self._state_lock:
            return dict(self._progress)

    def _set_progress(self, **values):
        with self._state_lock:
            self._progress = values

    def import_sources(self, path, source_format='auto', account='default'):
        return self._import(lambda: self._selection(path, source_format), account)

    def import_local(self, account='default'):
        return self._import(self._local_selection, account)

    def _local_selection(self):
        selected = [(kind, path) for kind, path, _ in local_sources(*default_roots())]
        zcode = Path.home() / '.zcode/cli/db/db.sqlite'
        if zcode.is_file():
            selected.append(('zcode', zcode))
        return selected, [], 0

    def _import(self, selection, account):
        account = account.strip()
        if not account:
            raise ValueError('Enter an account label. Reuse it for later exports from that account.')
        if not self._import_lock.acquire(blocking=False):
            raise ValueError('An import is already running.')
        completed = 0
        try:
            self._set_progress(running=True, completed=0, total=None)
            selected, ignored, excluded = selection()
            changes = {kind: Counter(new=0, updated=0, unchanged=0, protected=0, removed=0)
                       for kind in ('conversations', 'nodes', 'memories')}
            warnings = Counter(unrecognized_format=len(ignored)) if ignored else Counter()
            batches = []
            error = None
            with closing(connect(self.database)) as db:
                for kind, source in selected:
                    self._set_progress(running=True, completed=completed, total=len(selected))
                    try:
                        result = run_batch(db, [(kind, source, IMPORTERS[kind])], account, 'gui')
                    except Exception as failure:
                        # run_batch has already recorded a content-free failure.
                        error = f'Import stopped ({type(failure).__name__}). Check the selected export format; close native apps before importing their stores.'
                        break
                    completed += 1
                    batches.append(result['batch_id'])
                    warnings.update(result['warnings'])
                    for record_type, counts in result['changes'].items():
                        changes[record_type].update(counts)
            return {
                'completed': completed, 'total': len(selected), 'batches': batches,
                'formats': dict(Counter(kind for kind, _ in selected)),
                'changes': {kind: dict(counts) for kind, counts in changes.items()},
                'warnings': dict(warnings), 'other_formats': excluded, 'error': error,
            }
        finally:
            state = self.progress()
            self._set_progress(running=False, completed=completed, total=state['total'])
            self._import_lock.release()

    def search(self, query, provider='', account=''):
        if not query.strip():
            return {'groups': [], 'candidate_limit_reached': False, 'candidates_examined': 0}
        with closing(connect(self.database, read_only=True)) as db:
            return search_conversations(db, query, 50, [provider] if provider else None,
                                        [account] if account else None)

    def library(self, provider='', account='', offset=0):
        offset = max(0, int(offset))
        with closing(connect(self.database, read_only=True)) as db:
            rows = db.execute("""
                SELECT * FROM (
                    SELECT 'conversation' AS group_type, a.provider, a.label AS account,
                           c.source_id AS conversation_id, NULL AS memory_id, c.title,
                           coalesce(c.updated_at, c.created_at) AS date
                    FROM conversations c JOIN source_accounts a ON a.id=c.account_id
                    UNION ALL
                    SELECT 'memory', a.provider, a.label, NULL, m.source_id, m.title, m.created_at
                    FROM memories m JOIN source_accounts a ON a.id=m.account_id
                ) WHERE (?='' OR provider=?) AND (?='' OR account=?)
                ORDER BY date DESC, provider, account, group_type, conversation_id, memory_id
                LIMIT 31 OFFSET ?
            """, (provider, provider, account, account, offset)).fetchall()
        return {'groups': [dict(row) for row in rows[:30]],
                'next_offset': offset + 30 if len(rows) > 30 else None}

    def conversation(self, provider, account, source_id, offset=0):
        with closing(connect(self.database, read_only=True)) as db:
            page = get_conversation(db, provider, account, source_id, int(offset), 20)
        # The reader loads the exact continuation separately, without a display ellipsis.
        for message in page['messages']:
            if message['truncated']:
                message['text'] = message['text'][:4000]
        return page

    def message(self, provider, account, source_id, node_id, offset):
        with closing(connect(self.database, read_only=True)) as db:
            return get_message(db, provider, account, source_id, node_id, int(offset))

    def memory(self, provider, account, source_id, offset=0):
        with closing(connect(self.database, read_only=True)) as db:
            row = db.execute(
                'SELECT m.title, m.kind, m.text, m.created_at FROM memories m '
                'JOIN source_accounts a ON a.id=m.account_id '
                'WHERE a.provider=? AND a.label=? AND m.source_id=?',
                (provider, account, source_id),
            ).fetchone()
        if row is None:
            raise LookupError('Saved context not found.')
        result = dict(row)
        offset = max(0, int(offset))
        end = offset + 4000
        result.update(text=row['text'][offset:end], offset=offset,
                      next_offset=end if end < len(row['text']) else None,
                      total_chars=len(row['text']))
        return result


def ui_call(function):
    """Return actionable errors without forwarding private parser/SQL messages."""
    @wraps(function)
    def wrapped(*args, **kwargs):
        try:
            return {'ok': True, 'data': function(*args, **kwargs)}
        except FileNotFoundError:
            message = 'That source no longer exists. Choose an existing file or folder.'
        except sqlite3.OperationalError:
            message = 'The operation could not finish. For search, check the FTS expression; for imports, check whether another process is writing the archive.'
        except Exception as error:
            message = f'Operation failed ({type(error).__name__}). Check the selected input and try again.'
        return {'ok': False, 'error': message}
    return wrapped


class GuiBridge:
    # Only these methods are exposed. Never attach a public window/service object.
    def __init__(self, service, chooser):
        self._service = service
        self._chooser = chooser

    @ui_call
    def status(self):
        return self._service.status()

    @ui_call
    def choose(self, folder=True):
        return self._chooser(bool(folder))

    @ui_call
    def preview(self, path, source_format):
        return self._service.preview(path, source_format)

    @ui_call
    def import_sources(self, path, source_format, account):
        return self._service.import_sources(path, source_format, account)

    @ui_call
    def import_local(self, account='default'):
        return self._service.import_local(account)

    @ui_call
    def progress(self):
        return self._service.progress()

    @ui_call
    def search(self, query, provider, account):
        return self._service.search(query, provider, account)

    @ui_call
    def library(self, provider='', account='', offset=0):
        return self._service.library(provider, account, offset)

    @ui_call
    def conversation(self, provider, account, source_id, offset=0):
        return self._service.conversation(provider, account, source_id, offset)

    @ui_call
    def message(self, provider, account, source_id, node_id, offset):
        return self._service.message(provider, account, source_id, node_id, offset)

    @ui_call
    def memory(self, provider, account, source_id, offset=0):
        return self._service.memory(provider, account, source_id, offset)


def page_html():
    assets = files('archive_mcp').joinpath('gui_assets')
    def data_uri(name, mime):
        return f'data:{mime};base64,' + base64.b64encode(assets.joinpath(name).read_bytes()).decode('ascii')
    style = assets.joinpath('style.css').read_text(encoding='utf-8')
    for token, name in [('CHAMBER', 'chamber.png'), ('DOOR', 'door.png'), ('OVERHEAD', 'basin-overhead.png'), ('BOTTLE', 'apothecary-bottle.png')]:
        style = style.replace(f'__{token}__', data_uri(name, 'image/png'))
    logos = {name: data_uri(f'logos/{name}.svg', 'image/svg+xml') for name in
             ('openai', 'codex', 'claude', 'gemini', 'deepseek', 'grok', 'qwen', 'opencode', 'antigravity', 'notebooklm')}
    return (assets.joinpath('index.html').read_text(encoding='utf-8')
            .replace('/* BUNDLED_STYLE */', style)
            .replace('/* BUNDLED_LOGOS */', json.dumps(logos))
            .replace('/* BUNDLED_I18N */', assets.joinpath('i18n.js').read_text(encoding='utf-8'))
            .replace('/* BUNDLED_SCRIPT */', assets.joinpath('app.js').read_text(encoding='utf-8'))
            .replace('/* BUNDLED_SCENE */', assets.joinpath('scene.js').read_text(encoding='utf-8')))


def main(argv=None):
    parser = argparse.ArgumentParser(description='Open the local AI Pensieve desktop prototype.')
    parser.add_argument('--database', default='runtime/archive.sqlite', help='Local SQLite archive (default: runtime/archive.sqlite in the current directory)')
    args = parser.parse_args(argv)
    try:
        import webview
    except ImportError:
        parser.exit(1, 'Install the optional GUI first: python -m pip install ".[gui]"\n')
    try:
        service = GuiService(args.database)
    except Exception as error:
        parser.exit(1, f'Could not open the local archive ({type(error).__name__}). Check --database and the directory permissions.\n')
    def choose(folder):
        result = window.create_file_dialog(webview.FileDialog.FOLDER if folder else webview.FileDialog.OPEN)
        return result[0] if result else None
    bridge = GuiBridge(service, choose)
    webview.settings['ALLOW_DOWNLOADS'] = False
    webview.settings['ALLOW_FILE_URLS'] = False
    window = webview.create_window('AI Pensieve', html=page_html(), js_api=bridge,
                                  width=1240, height=840, min_size=(900, 650),
                                  background_color='#030608', text_select=True)
    window.events.closing += lambda: False if service.progress()['running'] else None
    webview.start(private_mode=True, http_server=False, debug=False)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
