# AI Pensieve

An early-preview desktop archive for AI conversations, with a wooden-door
entrance, illustrated memory chamber, import bottles, search and original-thread
reading. English and Chinese interface. Native GUI tested on macOS; Windows/Linux
GUI behavior remains unverified and requires a working native webview backend.

The desktop package installs the matching `ai-pensieve-mcp` core and its GUI
dependencies. It provides both `ai-pensieve` and `pensieve` commands.

```sh
uvx ai-pensieve
```

Or install with pipx, then launch:

```sh
pipx install ai-pensieve
pensieve
```

These commands require uv or pipx to be installed. Installation downloads packages;
ordinary GUI import/search runs locally with no telemetry or model calls.
You explicitly choose what to import. MCP clients may send retrieved excerpts to
their model provider.

Use `pensieve --database /path/to/archive.sqlite` to open an existing archive.
Without that option, the app uses its persistent user-data directory, independent
of the working directory and the tool's installation cache. Uninstalling the tool
does not delete the archive.

[Setup and platform requirements](https://github.com/AS-XS/AI-Pensieve-MCP/blob/main/docs/GUI.md) ·
[Privacy](https://github.com/AS-XS/AI-Pensieve-MCP/blob/main/docs/privacy/README.md) ·
[Source and Apache-2.0 license](https://github.com/AS-XS/AI-Pensieve-MCP)
