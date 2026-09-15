"""Copyable local MCP configuration; never edits client settings."""
import json
from pathlib import Path
import shutil
import sys


def connection_config(database, client):
    if client not in ('codex', 'claude-desktop', 'cursor', 'generic'):
        raise ValueError('Select a documented local MCP client.')
    uvx = shutil.which('uvx')
    if uvx:
        entry = {'command': uvx, 'args': ['ai-pensieve-mcp', str(database)]}
        launcher = 'Uses uvx. Keep uv installed.'
    else:
        entry = {'command': sys.executable,
                 'args': ['-m', 'archive_mcp.mcp_server', str(database)],
                 'env': {'PYTHONPATH': str(Path(__file__).resolve().parents[1])}}
        launcher = 'Uses this installation. Copy a new configuration if you move or reinstall it.'
    if client == 'codex':
        lines = ['[mcp_servers.ai-pensieve-mcp]']
        for key in ('command', 'args'):
            lines.append(f'{key} = {json.dumps(entry[key], ensure_ascii=False)}')
        if entry.get('env'):
            lines.extend(['', '[mcp_servers.ai-pensieve-mcp.env]',
                          'PYTHONPATH = ' + json.dumps(entry['env']['PYTHONPATH'], ensure_ascii=False)])
        text = '\n'.join(lines) + '\n'
    else:
        text = json.dumps(entry if client == 'generic' else
                          {'mcpServers': {'ai-pensieve-mcp': entry}}, indent=2, ensure_ascii=False)
    return {'configuration': text, 'launcher': launcher}
