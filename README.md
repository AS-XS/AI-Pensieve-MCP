# [AI Pensieve MCP](https://github.com/AS-XS/AI-Pensieve-MCP)

中文版：[README](README.zh-CN.md) · [客户端设置](docs/AI_CLIENTS.zh-CN.md) · [用户指南](docs/USER_GUIDE.zh-CN.md)

Search your imported AI conversations from your preferred MCP client.

> **Privacy:** the archive is stored locally and MCP access is read-only.
> Retrieved excerpts may be sent to your connected AI provider.
> [How your data is handled](docs/privacy/README.md)

Imports include ChatGPT, Claude, Gemini, DeepSeek, Grok, and supported coding
sessions. NotebookLM support is notebook metadata only.
[Full import coverage](docs/COMPATIBILITY.md)

## 1. Install

Download the project from [GitHub](https://github.com/AS-XS/AI-Pensieve-MCP)
using **Code → Download ZIP**, extract it, and open a terminal in that folder.
Python 3.10+ with SQLite FTS5 is required. Dependency installation
downloads packages; ordinary archive import and search run locally.

On macOS or Linux:

```sh
mkdir -p imports runtime
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force imports, runtime | Out-Null
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Open the magical memory room with `pensieve`: [optional GUI setup and guide](docs/GUI.md).
It provides folder import, search, and a conversation reader.

## 2. Import selected history

To verify setup first, [run the synthetic demo](docs/DEMO.md). It checks imports
and a real MCP connection using only bundled examples.

Follow the [app export guide](docs/EXPORT_GUIDE.md), extract any ZIP,
and copy one account's selected files/folders into `imports/account-one/`.
Keep different accounts in separate folders and import each with its own label
using the [user guide](docs/USER_GUIDE.md#separate-accounts).

On macOS or Linux:

```sh
PYTHONPATH=src .venv/bin/python -m archive_mcp import-auto runtime/archive.sqlite imports/account-one --account account-one
PYTHONPATH=src .venv/bin/python -m archive_mcp check runtime/archive.sqlite
```

On Windows PowerShell:

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
.\.venv\Scripts\python.exe -m archive_mcp import-auto runtime\archive.sqlite imports\account-one --account account-one
.\.venv\Scripts\python.exe -m archive_mcp check runtime\archive.sqlite
```

Imports leave original files unchanged. A successful check reports `"ok": true`.
Unchanged imports do not duplicate canonical records. Import reports accumulate. See the
[user guide](docs/USER_GUIDE.md) for import reports, refreshes, and native sessions.

## 3. Connect and use

Check [client support and verification status](docs/COMPATIBILITY.md#mcp-clients),
then follow the [setup guide](docs/AI_CLIENTS.md). After connecting,
ask it to check archive status, then try:

> Search my archive for discussions about machine learning. Show the source
> conversations and dates supporting your answer.

> Find discussions of my project across different AI providers and compare
> the decisions recorded in them.

[More example prompts and what each tool does](docs/EXAMPLE_PROMPTS.md).

The AI searches the imported snapshot; new conversations appear after another
import or refresh. For older archives, follow the
[upgrade instructions](docs/MCP_TOOLS.md#upgrading-an-existing-archive).

Licensed under [Apache License 2.0](LICENSE).
