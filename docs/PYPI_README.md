# AI Pensieve MCP

Import supported AI conversations and coding sessions into a local SQLite
archive, then search and cross-reference them through read-only MCP tools with
source attribution. No paid processing API, hosted database, or model is needed
for import and keyword search.

<!-- mcp-name: io.github.AS-XS/ai-pensieve-mcp -->

Run against an existing imported archive with uv:

```sh
uvx ai-pensieve-mcp /absolute/path/to/archive.sqlite
```

In an MCP client, set command `uvx` and arguments `ai-pensieve-mcp` and your
absolute database path. The process speaks STDIO; it does not open a desktop
window. For the illustrated GUI, install the separate `ai-pensieve` package.

CLI import/check commands are available through:

```sh
uvx --from ai-pensieve-mcp pensieve-archive --help
```

Installation downloads packages. Imported archives remain local and source
exports are unchanged. A connected AI client may forward retrieved text to its
model provider. This is an early release; format and client verification limits
are documented below.

[Installation](https://github.com/AS-XS/AI-Pensieve-MCP/blob/main/docs/INSTALLATION.md) ·
[Import guide](https://github.com/AS-XS/AI-Pensieve-MCP/blob/main/docs/USER_GUIDE.md) ·
[Supported sources and clients](https://github.com/AS-XS/AI-Pensieve-MCP/blob/main/docs/COMPATIBILITY.md) ·
[Privacy](https://github.com/AS-XS/AI-Pensieve-MCP/blob/main/docs/privacy/README.md) ·
[Source and Apache-2.0 license](https://github.com/AS-XS/AI-Pensieve-MCP)
