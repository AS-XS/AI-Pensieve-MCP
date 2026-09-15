# Isolated package installation

Version **0.1.0** is published on PyPI: [desktop](https://pypi.org/project/ai-pensieve/)
and [MCP core](https://pypi.org/project/ai-pensieve-mcp/). Fresh uvx and pipx
installations, native GUI launch, and STDIO were verified on macOS with Python
3.13. The [source installation](SOURCE_INSTALL.md) remains available.

Version 0.2.0 is prepared for publication with a **Connect to an AI** shelf
action and `pensieve --demo` for a temporary archive of invented exports.
The published 0.1.0 packages do not include these additions.

## Desktop

With [uv](https://docs.astral.sh/uv/getting-started/installation/)
already installed:

```sh
uvx ai-pensieve
```

For a persistent command, with [pipx](https://pipx.pypa.io/stable/installation/):

```sh
pipx install ai-pensieve
pensieve
```

Both commands open the same GUI. pipx must have its application directory on
PATH; follow its installation instructions if `pensieve` is not found.
The `ai-pensieve` package installs the matching `ai-pensieve-mcp[gui]` core.

Native GUI launch is tested on macOS with Python 3.13. Windows requires WebView2;
Linux requires a supported GTK or Qt backend. Their GUI flows remain unverified.
See [GUI setup](GUI.md) for platform requirements and persistent archive locations.
Use `--database /path/to/archive.sqlite` to select an existing archive.

## MCP without the desktop dependencies

```sh
uvx ai-pensieve-mcp /absolute/path/to/archive.sqlite
```

This runs the read-only STDIO server, not the GUI. The database must already be
initialized and imported. Configure your MCP client with command `uvx` and
arguments `ai-pensieve-mcp`, `/absolute/path/to/archive.sqlite`. It requires no
checkout, Python module path, or `PYTHONPATH`. Client setup remains subject to
its [documented verification status](COMPATIBILITY.md#mcp-clients).

The core also exposes `pensieve-archive` for CLI imports and checks. For example,
use `uvx --from ai-pensieve-mcp pensieve-archive --help`. Developer demo/evaluation
commands still use the synthetic fixtures in a source checkout.

Installation downloads packages from PyPI. GUI import/search runs locally;
connected MCP clients may send retrieved text to their model provider.
There is no automatic source discovery/import on launch. Package installation,
upgrades, and uninstalling do not move or delete archives.
