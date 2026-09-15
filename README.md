# [AI Pensieve MCP](https://github.com/AS-XS/AI-Pensieve-MCP)

中文版：[README](README.zh-CN.md) · [客户端设置](docs/AI_CLIENTS.zh-CN.md) · [用户指南](docs/USER_GUIDE.zh-CN.md)

Search your imported AI conversations locally, either through the illustrated
desktop room or from an MCP client.

> **Privacy:** the archive stays on your computer and MCP tools are read-only.
> Retrieved excerpts may be sent to the AI provider connected to your client.
> [How your data is handled](docs/privacy/README.md)

## Install

Open the desktop with [uv](https://docs.astral.sh/uv/getting-started/installation/):

```sh
uvx ai-pensieve
```

For a persistent command:

```sh
pipx install ai-pensieve
pensieve
```

To run only the read-only MCP server against an existing archive:

```sh
uvx ai-pensieve-mcp /absolute/path/to/archive.sqlite
```

See the [package installation guide](docs/INSTALLATION.md) for client setup,
platform requirements, persistent archive locations, and source installation.

## Use the desktop

1. Open the wooden door and touch the Pensieve.
2. Choose **Import a memory**, then select a provider bottle, **Unmarked** for
   auto-detection, or **Find & import local sessions**.
3. Choose an exported file or folder, inspect the selection, and pour it into
   the basin. The original files stay unchanged.
4. Choose **Search the waters**, search by keyword, and open a smoke result to
   read the original thread.

The GUI imports ChatGPT, Claude, Gemini, DeepSeek, Grok, and supported coding
sessions. NotebookLM currently provides notebook metadata only. See the
[full compatibility matrix](docs/COMPATIBILITY.md) and [export guide](docs/EXPORT_GUIDE.md).

## Connect an AI client

Import an archive first, then follow [AI client setup](docs/AI_CLIENTS.md) and
check the [client verification status](docs/COMPATIBILITY.md#mcp-clients).
The current source GUI also offers **shelf → Connect to an AI** and a temporary
`pensieve --demo` mode; these are not in PyPI 0.1.0 yet.
Try prompts such as:

> Search my archive for discussions about machine learning. Show the source
> conversations and dates supporting your answer.

> Find discussions of my project across different AI providers and compare the
> decisions recorded in them.

[More example prompts and tool details](docs/EXAMPLE_PROMPTS.md).

The archive is a local snapshot: import or refresh again when new conversations
should appear. For command-line imports, custom source folders, and revision and
deduplication rules, see the [user guide](docs/USER_GUIDE.md).

Licensed under [Apache License 2.0](LICENSE).

<!-- mcp-name: io.github.AS-XS/ai-pensieve-mcp -->
