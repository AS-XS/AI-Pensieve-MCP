# AI Client Setup

AI Pensieve MCP is a local STDIO MCP server. Each compatible AI client
starts the same Python process and communicates with it through standard input
and output. The archive server needs no port, hosted service, or API key;
the AI client may have its own account and model requirements.

Non-OpenAI references rechecked 2026-09-10; OpenAI checked 2026-09-09.
Each section states its verification status. A setup example means the official
configuration contract was checked; it does not mean this archive was tested
in that app. See the [client evidence matrix](COMPATIBILITY.md#mcp-clients) and
[connections not supported](COMPATIBILITY.md#connections-not-supported-by-this-project).
Menu labels and supported platforms depend on client version.

Complete the main README setup and import steps first. The database should exist
at `runtime/archive.sqlite` before registering the server.

## Paths

Examples use the repository folder `AI-Pensieve-MCP` and server label
`ai-pensieve-mcp`. ZIP downloads may extract to a folder with a branch suffix;
use its actual path. Existing checkouts and registrations named
`personal-ai-archive` still work; update an existing registration rather than
adding a duplicate. The Python module remains `archive_mcp`.

Use absolute paths in client configuration. Replace the examples below with the
location where you downloaded the project. Keep shell paths quoted so locations
containing spaces work too.

| Value | macOS or Linux | Windows |
| --- | --- | --- |
| Python | `/absolute/path/AI-Pensieve-MCP/.venv/bin/python` | `C:/absolute/path/AI-Pensieve-MCP/.venv/Scripts/python.exe` |
| Module path | `/absolute/path/AI-Pensieve-MCP/src` | `C:/absolute/path/AI-Pensieve-MCP/src` |
| Database | `/absolute/path/AI-Pensieve-MCP/runtime/archive.sqlite` | `C:/absolute/path/AI-Pensieve-MCP/runtime/archive.sqlite` |

Forward slashes in the Windows JSON examples avoid doubled backslash escaping.
Windows substitutions below illustrate path syntax only; they are not proof
that a particular app/version supports native Windows. Use them only where the
installed client supports local STDIO on Windows. No Windows registration was
executed in this review.

## Codex CLI and desktop

**Status: documented configuration; current app integration unverified.** Earlier
local registration is recorded, but the SDK demo is not a Codex app test.

On macOS or Linux:

```sh
codex mcp add ai-pensieve-mcp \
  --env "PYTHONPATH=/absolute/path/AI-Pensieve-MCP/src" \
  -- "/absolute/path/AI-Pensieve-MCP/.venv/bin/python" \
  -m archive_mcp.mcp_server \
  "/absolute/path/AI-Pensieve-MCP/runtime/archive.sqlite"
```

On Windows PowerShell:

```powershell
codex mcp add ai-pensieve-mcp `
  --env "PYTHONPATH=C:\absolute\path\AI-Pensieve-MCP\src" `
  -- "C:\absolute\path\AI-Pensieve-MCP\.venv\Scripts\python.exe" `
  -m archive_mcp.mcp_server `
  "C:\absolute\path\AI-Pensieve-MCP\runtime\archive.sqlite"
```

Check the registration with:

```sh
codex mcp list
```

Codex CLI and the IDE extension share MCP configuration with the compatible
desktop client on the same host. Current OpenAI documentation calls that client
the ChatGPT desktop app; earlier project notes call it Codex desktop. This
does not apply to ChatGPT web. Alternatively, open **Settings > MCP servers**, choose
**Add server**, select **STDIO**, and enter the command, arguments, and
environment value from the paths table. Save and restart the client. Use `/mcp`
to inspect connected servers.

Codex stores global configuration in `~/.codex/config.toml`. A trusted project
can instead use `.codex/config.toml` for project-scoped configuration.

## Claude Code

**Status: documented configuration; archive integration untested.** This section
is for Claude Code, not Claude web or mobile.

Use user scope to make the archive available in every Claude Code project.

On macOS or Linux:

```sh
claude mcp add \
  --scope user \
  --env "PYTHONPATH=/absolute/path/AI-Pensieve-MCP/src" \
  --transport stdio \
  ai-pensieve-mcp \
  -- "/absolute/path/AI-Pensieve-MCP/.venv/bin/python" \
  -m archive_mcp.mcp_server \
  "/absolute/path/AI-Pensieve-MCP/runtime/archive.sqlite"
```

On Windows PowerShell:

```powershell
claude mcp add `
  --scope user `
  --env "PYTHONPATH=C:\absolute\path\AI-Pensieve-MCP\src" `
  --transport stdio `
  ai-pensieve-mcp `
  -- "C:\absolute\path\AI-Pensieve-MCP\.venv\Scripts\python.exe" `
  -m archive_mcp.mcp_server `
  "C:\absolute\path\AI-Pensieve-MCP\runtime\archive.sqlite"
```

Verify it with:

```sh
claude mcp get ai-pensieve-mcp
claude mcp list
```

Inside Claude Code, `/mcp` shows the server and its tools.

## Claude Desktop

**Status: documented configuration; archive integration untested.** The manual
paths below are documented for macOS and Windows; no Linux setup is claimed here.

For a local checkout, add the server to `claude_desktop_config.json`:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

macOS:

```json
{
  "mcpServers": {
    "ai-pensieve-mcp": {
      "command": "/absolute/path/AI-Pensieve-MCP/.venv/bin/python",
      "args": [
        "-m",
        "archive_mcp.mcp_server",
        "/absolute/path/AI-Pensieve-MCP/runtime/archive.sqlite"
      ],
      "env": {
        "PYTHONPATH": "/absolute/path/AI-Pensieve-MCP/src"
      }
    }
  }
}
```

Windows:

```json
{
  "mcpServers": {
    "ai-pensieve-mcp": {
      "command": "C:/absolute/path/AI-Pensieve-MCP/.venv/Scripts/python.exe",
      "args": [
        "-m",
        "archive_mcp.mcp_server",
        "C:/absolute/path/AI-Pensieve-MCP/runtime/archive.sqlite"
      ],
      "env": {
        "PYTHONPATH": "C:/absolute/path/AI-Pensieve-MCP/src"
      }
    }
  }
}
```

Preserve any existing entries inside `mcpServers`. Fully quit Claude Desktop,
not just its window, and reopen it after saving the file. Claude Desktop's
current one-click local integration format is a `.mcpb` desktop extension; the
JSON configuration above remains appropriate for a local developer checkout.

## Antigravity CLI and IDE

**Status: documented configuration; current version compatibility unverified.**
A local tool-call check was recorded on 2026-09-04 without the client version or
CLI/IDE surface. It does not validate current versions or every platform.

Antigravity CLI and IDE share the same global MCP configuration:

- macOS, Linux, and Windows user home: `~/.gemini/config/mcp_config.json`
- Windows expanded form: `%USERPROFILE%\.gemini\config\mcp_config.json`

Use the global configuration here. Workspace-only discovery is **unverified**:
official documentation lists `.agents/mcp_config.json`, while the earlier local
check found different behavior. The old unversioned plugin workaround is
removed from these instructions; no working workspace setup is claimed.

Use this configuration on macOS or Linux:

```json
{
  "mcpServers": {
    "ai-pensieve-mcp": {
      "command": "/absolute/path/AI-Pensieve-MCP/.venv/bin/python",
      "args": [
        "-m",
        "archive_mcp.mcp_server",
        "/absolute/path/AI-Pensieve-MCP/runtime/archive.sqlite"
      ],
      "env": {
        "PYTHONPATH": "/absolute/path/AI-Pensieve-MCP/src"
      }
    }
  }
}
```

On Windows, use the Windows JSON entry from the Claude Desktop section; the
`mcpServers` structure is the same.

In Antigravity IDE, open the `...` menu in the agent side panel, choose **MCP
Servers > Manage MCP Servers > View raw config**, add the entry, and refresh the
server list. In Antigravity CLI, enter `/mcp` to open the manager, inspect the
connection, and reload configuration.

## Cursor

**Status: documented configuration; archive integration untested.** Applies to
a local client with STDIO support, not a cloud agent expecting a server URL.

Open Cursor's **Customize** page, or create `~/.cursor/mcp.json` for
all projects. A project-only configuration goes in `.cursor/mcp.json`.

Copy the `mcpServers` JSON entry shown in the Claude Desktop section and add
`"type": "stdio"` inside the `ai-pensieve-mcp` server object, alongside
`command`. Cursor's current field table marks it required. Restart Cursor after
saving, then check that `ai-pensieve-mcp` and its eleven tools appear.

## Gemini CLI

**Status: documented configuration; archive integration untested.** Gemini Apps
web/mobile is not supported by these instructions.

Add the same `mcpServers` JSON entry to:

- macOS or Linux: `~/.gemini/settings.json`
- Windows: `%USERPROFILE%\.gemini\settings.json`
- Project only: `.gemini/settings.json`

Restart Gemini CLI, then use `/mcp list`. This is Gemini CLI's configuration;
Antigravity uses the separate path documented above.

## GitHub Copilot CLI

**Status: documented configuration; archive integration untested.** These
instructions do not configure Microsoft Copilot chat or the VS Code extension.

On macOS or Linux:

```sh
copilot mcp add ai-pensieve-mcp \
  --env "PYTHONPATH=/absolute/path/AI-Pensieve-MCP/src" \
  -- "/absolute/path/AI-Pensieve-MCP/.venv/bin/python" \
  -m archive_mcp.mcp_server \
  "/absolute/path/AI-Pensieve-MCP/runtime/archive.sqlite"
```

On Windows PowerShell:

```powershell
copilot mcp add ai-pensieve-mcp `
  --env "PYTHONPATH=C:\absolute\path\AI-Pensieve-MCP\src" `
  -- "C:\absolute\path\AI-Pensieve-MCP\.venv\Scripts\python.exe" `
  -m archive_mcp.mcp_server `
  "C:\absolute\path\AI-Pensieve-MCP\runtime\archive.sqlite"
```

Verify with `copilot mcp get ai-pensieve-mcp` or `copilot mcp list`.
Copilot CLI stores user configuration at `~/.copilot/mcp-config.json`. It does
not read VS Code's `.vscode/mcp.json`.

## Grok Build

**Status: documented configuration; archive integration untested.** Grok Chat
web/mobile is not supported by these instructions. Grok Build history import
is also not supported by this project.

Grok Build is xAI's coding harness, distinct from the Grok chat export that this
project imports. Add this to `~/.grok/config.toml`:

```toml
[mcp_servers.ai-pensieve-mcp]
command = "/absolute/path/AI-Pensieve-MCP/.venv/bin/python"
args = ["-m", "archive_mcp.mcp_server", "/absolute/path/AI-Pensieve-MCP/runtime/archive.sqlite"]
env = { PYTHONPATH = "/absolute/path/AI-Pensieve-MCP/src" }
```

Verify with `grok mcp list` and diagnose with
`grok mcp doctor ai-pensieve-mcp`. Native Windows setup is unverified;
the reference above establishes the TOML contract, not platform compatibility.

## OpenCode

**Status: documented v2 configuration; archive integration untested.** This
example is not a verified setup for v1 or other configuration versions.

Add this server to the user or project `opencode.jsonc`. OpenCode v2 keeps
server definitions under `mcp.servers`:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "servers": {
      "ai-pensieve-mcp": {
        "type": "local",
        "command": [
          "/absolute/path/AI-Pensieve-MCP/.venv/bin/python",
          "-m",
          "archive_mcp.mcp_server",
          "/absolute/path/AI-Pensieve-MCP/runtime/archive.sqlite"
        ],
        "environment": {
          "PYTHONPATH": "/absolute/path/AI-Pensieve-MCP/src"
        }
      }
    }
  }
}
```

On Windows, replace the three paths with the forward-slash Windows paths from
the paths table. Use OpenCode's MCP manager to list the connected tools.

## Cline, Roo Code, and Windsurf

**Status for each client below: documented configuration; archive integration
untested.** History import is not supported for any of these clients.

Each client's official guide documents the `mcpServers` structure used in the
Claude Desktop example. Use the client-specific location below.

Cline's current guide lists the CLI file below separately from the IDE settings.
Do not assume the CLI and IDE automatically share a configuration file.

| Client | User configuration |
| --- | --- |
| Cline CLI | `~/.cline/mcp.json` |
| Cline IDE extension | **MCP Servers > Configure > Configure MCP Servers** |
| Roo Code | **MCP Servers > Edit Global MCP**; project-only: `.roo/mcp.json` |
| Windsurf / Cascade | `~/.codeium/windsurf/mcp_config.json` |

Use the Windows version of that JSON entry on Windows. These locations contain
client configuration only; they do not make those clients' conversation
histories importable by this archive.

The Windsurf reference now redirects to Devin Desktop's Cascade guide; it
still documents the `~/.codeium/windsurf/mcp_config.json` path above.

## Zed

**Status: documented configuration; archive integration untested.** Zed history
import is not supported by this project.

Open **Settings > AI > MCP Servers > Add Server > Add Local Server**, or add this to Zed's
settings file:

```json
{
  "context_servers": {
    "ai-pensieve-mcp": {
      "command": "/absolute/path/AI-Pensieve-MCP/.venv/bin/python",
      "args": [
        "-m",
        "archive_mcp.mcp_server",
        "/absolute/path/AI-Pensieve-MCP/runtime/archive.sqlite"
      ],
      "env": {
        "PYTHONPATH": "/absolute/path/AI-Pensieve-MCP/src"
      }
    }
  }
}
```

Use the forward-slash Windows paths from the paths table when Zed is running on
Windows.

## Qwen Code

**Status: documented configuration; archive integration untested.** This applies
to Qwen Code, not a Qwen model in another app or the Qwen chat website.

Add the same `mcpServers` JSON entry shown in the Claude Desktop section to
`~/.qwen/settings.json`, or use a project `.qwen/settings.json`. Restart Qwen
Code and use `/mcp` to inspect the connection.

## DeepSeek Harness

**Status: documented plugin configuration; archive integration untested.**
DeepSeek Chat is not supported by these instructions, and Harness history
import is not supported by this project.

DeepSeek Harness configures MCP as a Cordis plugin rather than through
`mcpServers` JSON. Add a plugin row to the Harness configuration or overlay:

```yaml
- id: mcp-ai-pensieve-mcp
  name: '@deepseek-ai/dsh-mcp-client'
  config:
    serverName: ai-pensieve-mcp
    transport: stdio
    command: /absolute/path/AI-Pensieve-MCP/.venv/bin/python
    args: ['-m', 'archive_mcp.mcp_server', '/absolute/path/AI-Pensieve-MCP/runtime/archive.sqlite']
    env:
      PYTHONPATH: /absolute/path/AI-Pensieve-MCP/src
```

Use the forward-slash Windows paths from the paths table on Windows. Launch the
harness with that overlay or patch enabled. Its tool names appear as
`mcp__ai-pensieve-mcp__<tool>`.

## Continue

**Status: documented configuration in Agent mode; archive integration
untested.** The documented MCP setup is not supported outside Agent mode.
Continue history import is not supported by this project.

Create `.continue/mcpServers/ai-pensieve-mcp.json` in the project where you
use Continue, then copy the `mcpServers` JSON configuration from the Claude
Desktop section into that file. Use the Windows version of the JSON entry on
Windows.

Continue detects JSON files in `.continue/mcpServers/` automatically. Restart
Continue after saving, switch to Agent mode, and confirm that the archive tools
are available.

## Other local MCP clients

**Status: unverified until the specific client and transport are checked.**
The server launch contract below is a reference for integrations, not a claim
that every MCP-branded client works with this archive:

```text
command: absolute path to the virtual-environment Python
args:    -m archive_mcp.mcp_server ABSOLUTE_DATABASE_PATH
env:     PYTHONPATH=ABSOLUTE_SRC_PATH
```

The process launching this configuration needs filesystem access to the Python
environment, source tree, and database on that host. Web-only clients cannot
launch this local STDIO process without a companion or execution bridge;
this project does not provide one.

Client support and history import support are separate. See the
[compatibility matrix and importer roadmap](COMPATIBILITY.md) for the audited
status of popular clients and provider exports.

## Test the connection

After restarting the client, try:

```text
Show the providers and date ranges available in my personal AI archive.
```

The expected tool is `archive_status`, returning source labels, counts, and date
ranges rather than message text. Tool selection remains the client's decision.
Then try a focused search:

```text
Search my personal AI archive for the phrase "example topic" and show only five results.
```

If the server does not connect, first confirm that all three configured paths
are absolute and that `runtime/archive.sqlite` exists.

## Official references

- [OpenAI local MCP setup](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)
- [Claude Code MCP setup](https://code.claude.com/docs/en/mcp)
- [Claude Desktop extensions](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop) and [manual local configuration](https://modelcontextprotocol.io/docs/develop/connect-local-servers)
- [Antigravity MCP setup](https://antigravity.google/docs/mcp)
- [Cursor MCP setup](https://prod.cursor.com/docs/mcp)
- [Gemini CLI MCP setup](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/tutorials/mcp-setup.md)
- [GitHub Copilot CLI MCP setup](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers)
- [Grok Build MCP setup](https://docs.x.ai/build/features/mcp-servers)
- [OpenCode MCP setup](https://opencode.ai/v2/docs/mcp-servers)
- [Cline MCP setup](https://docs.cline.bot/mcp/mcp-overview)
- [Roo Code MCP setup](https://docs.roocode.com/features/mcp/using-mcp-in-roo)
- [Windsurf MCP setup](https://docs.windsurf.com/windsurf/cascade/mcp)
- [Zed MCP setup](https://zed.dev/docs/ai/mcp)
- [Continue MCP setup](https://docs.continue.dev/customize/deep-dives/mcp)
- [Qwen Code MCP setup](https://qwenlm.github.io/qwen-code-docs/en/users/features/mcp/)
- [DeepSeek Harness MCP client](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/mcp/mcp-client/README.md)
