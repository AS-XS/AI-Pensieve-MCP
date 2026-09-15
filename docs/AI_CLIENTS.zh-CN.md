# AI 客户端设置（简明版）

AI Pensieve MCP 是一个本地 STDIO MCP 服务。兼容的 AI 客户端会启动同一个 Python 进程，并通过标准输入和标准输出与它通信。

服务本身不需要端口、云端服务或 API 密钥。AI 客户端可能有自己的账号、模型和版本要求。

本手册是常用设置的简明版。完整的客户端列表、官方参考链接和每个客户端的验证状态，请参阅英文版 [AI client setup](AI_CLIENTS.md) 和 [兼容性说明](COMPATIBILITY.md)。

## 通过包安装后连接

先导入档案，并从桌面藏书架底部复制数据库的绝对路径。通过 uv 安装时，客户端启动命令是 `uvx`，参数为 `ai-pensieve-mcp` 和数据库路径；不需要下载源码或设置 `PYTHONPATH`。

Codex 的 `~/.codex/config.toml`（或 `$CODEX_HOME/config.toml`）示例：

```toml
[mcp_servers.ai-pensieve-mcp]
command = "uvx"
args = ["ai-pensieve-mcp", "/absolute/path/to/archive.sqlite"]
```

Claude Desktop 和 Cursor 的 JSON 示例：

```json
{
  "mcpServers": {
    "ai-pensieve-mcp": {
      "command": "uvx",
      "args": ["ai-pensieve-mcp", "/absolute/path/to/archive.sqlite"]
    }
  }
}
```

Claude Desktop 中打开 **Settings → Developer → Edit Config**；Cursor 使用个人配置 `~/.cursor/mcp.json`。只合并这个服务条目，保留其他设置，然后重启客户端。若找不到 `uvx`，使用其可执行文件的绝对路径。Windows JSON 路径可使用正斜杠。

0.2.0 版的“藏书架 → 连接 AI 客户端”可以生成实际路径的配置，并在没有 uvx 时提供本次安装的 Python 启动方式。配置格式已于 2026-09-15 查阅官方文档；Codex CLI 有合成数据测试，Codex 桌面、Claude Desktop 和 Cursor 的实际连接仍未验证。详见[英文说明及官方链接](AI_CLIENTS.md#package-installation)。

## 源码安装的设置步骤

1. 完成[源码安装](SOURCE_INSTALL.md)及[导入步骤](USER_GUIDE.zh-CN.md)。
2. 确认数据库已经存在：`runtime/archive.sqlite`。
3. 在客户端配置中使用绝对路径。

三个主要路径如下：

| 内容 | macOS/Linux | Windows |
| --- | --- | --- |
| Python | `/absolute/path/AI-Pensieve-MCP/.venv/bin/python` | `C:/absolute/path/AI-Pensieve-MCP/.venv/Scripts/python.exe` |
| 源代码 | `/absolute/path/AI-Pensieve-MCP/src` | `C:/absolute/path/AI-Pensieve-MCP/src` |
| 数据库 | `/absolute/path/AI-Pensieve-MCP/runtime/archive.sqlite` | `C:/absolute/path/AI-Pensieve-MCP/runtime/archive.sqlite` |

请把示例中的路径替换成你实际下载项目的位置。路径中包含空格时，请保留引号。

## 通用启动方式

客户端需要启动以下本地进程：

```text
Python:   /absolute/path/AI-Pensieve-MCP/.venv/bin/python
参数:     -m archive_mcp.mcp_server /absolute/path/AI-Pensieve-MCP/runtime/archive.sqlite
环境变量: PYTHONPATH=/absolute/path/AI-Pensieve-MCP/src
```

Windows 使用 `.venv/Scripts/python.exe`，并把路径换成 Windows 路径。

## Codex CLI

macOS/Linux：

```sh
codex mcp add ai-pensieve-mcp \
  --env "PYTHONPATH=/absolute/path/AI-Pensieve-MCP/src" \
  -- "/absolute/path/AI-Pensieve-MCP/.venv/bin/python" \
  -m archive_mcp.mcp_server \
  "/absolute/path/AI-Pensieve-MCP/runtime/archive.sqlite"
codex mcp list
```

Windows PowerShell：

```powershell
codex mcp add ai-pensieve-mcp `
  --env "PYTHONPATH=C:\absolute\path\AI-Pensieve-MCP\src" `
  -- "C:\absolute\path\AI-Pensieve-MCP\.venv\Scripts\python.exe" `
  -m archive_mcp.mcp_server `
  "C:\absolute\path\AI-Pensieve-MCP\runtime\archive.sqlite"
codex mcp list
```

添加后重启客户端，并用 `/mcp` 查看已连接的服务器。当前记录中 Codex CLI 在 macOS 上做过有限的合成数据验证；桌面端和 IDE 集成仍不代表已验证。

## Claude Code

macOS/Linux：

```sh
claude mcp add \
  --scope user \
  --env "PYTHONPATH=/absolute/path/AI-Pensieve-MCP/src" \
  --transport stdio \
  ai-pensieve-mcp \
  -- "/absolute/path/AI-Pensieve-MCP/.venv/bin/python" \
  -m archive_mcp.mcp_server \
  "/absolute/path/AI-Pensieve-MCP/runtime/archive.sqlite"
claude mcp get ai-pensieve-mcp
claude mcp list
```

Claude Desktop 可以在其本地 MCP 配置文件中添加相同的 `command`、`args` 和 `env`。不同客户端的配置文件位置和字段可能不同；请先查看英文设置文档中的对应章节。

## Gemini CLI、Cursor 和其他客户端

许多支持本地 STDIO 的客户端都使用上面的启动合同。常见配置通常包含：

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

但客户端的配置字段可能不同：例如 Cursor 需要 `"type": "stdio"`，OpenCode 使用自己的配置结构，Zed 使用 `context_servers`。请不要把一个客户端的配置文件直接复制到另一个客户端。

本项目只提供本地 STDIO 服务，不提供 HTTP/SSE 地址、浏览器桥接、移动端连接或托管 MCP URL。客户端能够调用 MCP，并不代表它的历史记录格式可以被本项目导入。

## 测试连接

重启客户端后，先询问：

```text
显示我的个人 AI 档案中有哪些服务商和日期范围。
```

预期工具是 `archive_status`，它会返回来源标签、数量和日期范围，而不是完整消息文本。然后可以进行一个小范围搜索：

```text
在我的个人 AI 档案中搜索“example topic”，只显示五个结果。
```

如果服务没有连接，先检查三条路径是否都是绝对路径，并确认 `runtime/archive.sqlite` 存在。
