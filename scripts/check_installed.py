"""Smoke-test installed wheels, outside source imports, using invented data only."""
import asyncio
import json
from importlib.metadata import distribution
from pathlib import Path
import subprocess
import sysconfig
import tempfile

import archive_mcp
from archive_mcp.gui import GuiService, page_html
from archive_mcp.gui_demo import write_demo_sources
from mcp import Client
from mcp.client.stdio import StdioServerParameters, stdio_client


def executable(name):
    path = Path(sysconfig.get_path('scripts')) / name
    return path.with_suffix('.exe') if __import__('os').name == 'nt' else path


async def check_server(database):
    args = StdioServerParameters(command=str(executable('ai-pensieve-mcp')),
                                 args=[str(database), '--log', str(database.with_suffix('.jsonl'))],
                                 env={'PYTHONPATH': ''})
    async with Client(stdio_client(args), read_timeout_seconds=10) as client:
        tools = (await client.list_tools()).tools
        assert len(tools) == 13 and all(t.annotations.read_only_hint for t in tools)
        result = await client.call_tool('archive_status', {})
        assert not result.is_error
        assert result.structured_content['totals']['conversations'] == 1


def main():
    source = Path(__file__).resolve().parents[1] / 'src'
    assert source not in Path(archive_mcp.__file__).resolve().parents
    core = distribution('ai-pensieve-mcp')
    desktop = distribution('ai-pensieve')
    assert core.version == desktop.version
    for command in ('ai-pensieve', 'pensieve', 'ai-pensieve-mcp', 'pensieve-archive'):
        result = subprocess.run([str(executable(command)), '--help'], capture_output=True, text=True)
        assert result.returncode == 0, command
    page = page_html()
    assert 'BUNDLED_' not in page and '__BOTTLE__' not in page
    assert page.count('data:image/png;base64,') == 4
    assert page.count('data:image/svg+xml;base64,') == 10
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / 'sample.json'
        source.write_text(json.dumps([{'uuid': 'synthetic-install', 'name': 'Installation example',
            'created_at': '2026-01-01T00:00:00Z', 'updated_at': '2026-01-01T00:01:00Z',
            'chat_messages': [{'uuid': 'user-1', 'sender': 'human', 'text': 'Test archive installation.',
                               'created_at': '2026-01-01T00:00:00Z'}]}]))
        service = GuiService(root / 'archive.sqlite')
        result = service.import_sources(source, 'claude', 'synthetic-install')
        assert result['completed'] == 1 and not result['error']
        assert service.search('installation')['groups']
        asyncio.run(check_server(service.database))
        examples = root / 'examples'
        write_demo_sources(examples)
        demo = GuiService(root / 'demo.sqlite', examples)
        imported = demo.import_local('synthetic-demo')
        assert imported['completed'] == 2 and not imported['error']
        assert demo.status()['totals']['conversations'] == 4
        assert demo.search('garden')['groups']
    print('Installed core/desktop entrypoints, bundled artwork, temporary demo, synthetic import/search and 13-tool STDIO passed.')


if __name__ == '__main__':
    main()
