# Install from source

These instructions are for a downloaded or cloned source checkout. For the
short desktop command, use [package installation](INSTALLATION.md).

Download and extract the repository from
[GitHub](https://github.com/AS-XS/AI-Pensieve-MCP), or clone it. Open a terminal
in the extracted project folder. Use Python 3.10 or newer with SQLite FTS5.

macOS/Linux:

```sh
mkdir -p imports runtime
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
PYTHONPATH=src .venv/bin/python -m archive_mcp init runtime/archive.sqlite
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force imports, runtime
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:PYTHONPATH = (Resolve-Path src).Path
.\.venv\Scripts\python.exe -m archive_mcp init runtime\archive.sqlite
```

Python on Windows must also be version 3.10 or newer. Keep the environment and
`src` folder in place when configuring an AI client to use this checkout.
Dependencies download from PyPI; imports and ordinary search run locally.

Follow the [user guide](USER_GUIDE.md) to import an extracted export, or
[GUI installation](GUI.md#install-and-open) to add the optional desktop packages.
For invented data only, try the [developer demo](DEMO.md).

The CLI recipes in the user guide use this environment and `runtime/archive.sqlite`.
The packaged desktop instead defaults to its per-user application-data folder;
its library footer shows the actual path. Use the same database path when
connecting an AI client.
