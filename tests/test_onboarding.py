import asyncio
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from mcp import Client
from mcp.client.stdio import StdioServerParameters, stdio_client

from archive_mcp.client_config import connection_config
from archive_mcp.gui import GuiBridge, GuiService, main
from archive_mcp.gui_demo import write_demo_sources


class OnboardingTest(unittest.TestCase):
    def test_configs_preserve_literal_paths_and_client_structure(self):
        database = 'C:\\Example folder\\记忆 "notes"\\archive.sqlite'
        with patch('archive_mcp.client_config.shutil.which', return_value='/tools with spaces/uvx'):
            expected = {'command': '/tools with spaces/uvx',
                        'args': ['ai-pensieve-mcp', database]}
            for client in ('generic', 'claude-desktop', 'cursor'):
                parsed = json.loads(connection_config(database, client)['configuration'])
                self.assertEqual(parsed if client == 'generic' else parsed['mcpServers']['ai-pensieve-mcp'], expected)
            if sys.version_info >= (3, 11):
                import tomllib
                parsed = tomllib.loads(connection_config(database, 'codex')['configuration'])
                self.assertEqual(parsed['mcp_servers']['ai-pensieve-mcp'], expected)
        with self.assertRaises(ValueError):
            connection_config(database, 'unsupported-web-app')

    def test_python_fallback_launches_real_read_only_stdio(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = root / 'examples'
            write_demo_sources(sources)
            service = GuiService(root / 'archive space 记忆.sqlite')
            service.import_sources(sources, account='synthetic')
            before = service.database.read_bytes()
            with patch('archive_mcp.client_config.shutil.which', return_value=None):
                entry = json.loads(service.connection_config('generic')['configuration'])
                if sys.version_info >= (3, 11):
                    import tomllib
                    parsed = tomllib.loads(service.connection_config('codex')['configuration'])
                    self.assertEqual(parsed['mcp_servers']['ai-pensieve-mcp'], entry)

            async def verify():
                async with Client(stdio_client(StdioServerParameters(**entry)), read_timeout_seconds=10) as client:
                    tools = (await client.list_tools()).tools
                    self.assertEqual(len(tools), 13)
                    self.assertTrue(all(t.annotations.read_only_hint for t in tools))
                    result = await client.call_tool('archive_status', {})
                    self.assertFalse(result.is_error)
                    self.assertEqual(result.structured_content['totals']['conversations'], 4)
            asyncio.run(verify())
            self.assertEqual(service.database.read_bytes(), before)

    def test_demo_import_search_dedup_and_source_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = root / 'examples'
            write_demo_sources(sources)
            originals = {p: p.read_bytes() for p in sources.iterdir()}
            service = GuiService(root / 'archive.sqlite', sources)
            bridge = GuiBridge(service, lambda _: self.fail('Demo opened a personal source picker'))
            self.assertEqual(bridge.choose()['data'], str(sources.resolve()))
            self.assertEqual(service.status()['totals']['conversations'], 0)
            with patch('archive_mcp.gui.default_roots', side_effect=AssertionError('Personal discovery')):
                first = service.import_local('synthetic')
                again = service.import_local('synthetic')
            self.assertIsNone(first['error'])
            self.assertEqual(first['completed'], 2)
            self.assertEqual(service.status()['totals']['conversations'], 4)
            self.assertEqual(service.status()['totals']['messages'], 8)
            self.assertEqual(again['changes']['nodes']['new'], 0)
            self.assertEqual(again['changes']['nodes']['unchanged'], 8)
            for query in ('garden', 'research'):
                groups = service.search(query)['groups']
                self.assertEqual({g['provider'] for g in groups}, {'chatgpt', 'claude'})
            self.assertEqual({p: p.read_bytes() for p in originals}, originals)
            with self.assertRaises(ValueError):
                service.preview(root)
            self.assertFalse(bridge.connection_config('generic')['ok'])

    def test_demo_lifetime_ends_with_window_even_on_failure(self):
        for failure in (False, True):
            seen = []
            def window(service, webview):
                seen.append(service.database.parent)
                self.assertTrue(service.database.exists())
                self.assertEqual(service.preview(service.demo_sources)['files'], 2)
                if failure:
                    raise RuntimeError('Synthetic window failure')
                return 0
            with patch.dict(sys.modules, {'webview': SimpleNamespace()}), patch('archive_mcp.gui.open_window', side_effect=window):
                if failure:
                    with self.assertRaises(RuntimeError):
                        main(['--demo'])
                else:
                    self.assertEqual(main(['--demo']), 0)
            self.assertEqual(len(seen), 1)
            self.assertFalse(seen[0].exists())
