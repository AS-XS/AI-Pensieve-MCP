# 用户指南（简明版）

以下源码命令需要先完成[源码安装](SOURCE_INSTALL.md)，并在项目文件夹中运行。通过包安装时，可将 `PYTHONPATH=src .venv/bin/python -m archive_mcp`（Windows 中对应的 Python 启动部分）替换为 `uvx --from ai-pensieve-mcp pensieve-archive`，并将 `runtime/archive.sqlite` 替换为实际档案路径；桌面藏书架底部会显示此路径。新建命令行档案时，先通过同一启动方式执行 `init 数据库路径`。客户端配置请参阅[中文 AI 客户端设置](AI_CLIENTS.zh-CN.md)。支持的导出文件请参阅[导出指南](EXPORT_GUIDE.md)。

## 为不同账号分别导入

一次导入命令中的所有文件都会使用同一个账号标签。不同账号请放在不同文件夹，并分别运行导入命令。之后保持账号标签一致。

macOS/Linux：

```sh
PYTHONPATH=src .venv/bin/python -m archive_mcp import-auto runtime/archive.sqlite imports/account-one --account account-one
```

Windows PowerShell：

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
.\.venv\Scripts\python.exe -m archive_mcp import-auto runtime\archive.sqlite imports\account-one --account account-one
```

导入前先解压 ZIP。导入器会递归检查文件夹中的支持格式。原始文件不会被移动、重命名或删除。

## 使用自己的文件夹

不需要把导出文件复制到 `imports/`，可以直接使用现有路径：

macOS/Linux：

```sh
PYTHONPATH=src .venv/bin/python -m archive_mcp scan "/path/to/my AI exports"
PYTHONPATH=src .venv/bin/python -m archive_mcp import-auto runtime/archive.sqlite "/path/to/my AI exports" --account personal
```

Windows PowerShell：

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
.\.venv\Scripts\python.exe -m archive_mcp scan "D:\My AI exports"
.\.venv\Scripts\python.exe -m archive_mcp import-auto runtime\archive.sqlite "D:\My AI exports" --account personal
```

`scan` 只识别格式，不导入数据；`import-auto` 才会写入本地档案。支持多个文件或文件夹。把不同账号分开导入，即使它们的文本完全相同，也不会被合并。

## 检查导入结果

macOS/Linux：

```sh
PYTHONPATH=src .venv/bin/python -m archive_mcp import-report runtime/archive.sqlite
PYTHONPATH=src .venv/bin/python -m archive_mcp check runtime/archive.sqlite
```

Windows PowerShell：

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
.\.venv\Scripts\python.exe -m archive_mcp import-report runtime\archive.sqlite
.\.venv\Scripts\python.exe -m archive_mcp check runtime\archive.sqlite
```

常见警告：

- `unrecognized_format`：没有识别到支持的结构。
- `no_indexable_records`：没有可建立索引的消息节点或保存内容。
- `excluded_review_session`：识别出的 Codex 审核会话被排除。
- `import_failed`：导入失败；报告只保留异常类型。

`check` 检查数据库和索引的一致性，不是秘密扫描器，也不能证明所有历史记录都已导入。

## 查看和搜索对话

不使用关键词列出对话：

```sh
PYTHONPATH=src .venv/bin/python -m archive_mcp list-conversations runtime/archive.sqlite --limit 50
```

继续读取时，把返回的 `next_cursor` 原样作为 `--cursor` 传回，并保持筛选条件不变。导入、刷新、重建数据库或修改筛选条件后，要从头开始分页。分页过程不提供固定快照。

跨服务商或账号比较证据：

```sh
PYTHONPATH=src .venv/bin/python -m archive_mcp cross-reference runtime/archive.sqlite 'project' --candidate-limit 50 --limit 10
```

这个命令最多检查 10 个来源，每个来源最多 50 个候选结果，并显示最多 5 条证据。查看 `sources_unexamined`，不要把未检查的来源当成没有匹配结果。

## 广泛发现

对于不知道具体关键词的问题，可以使用来源均衡的调查：

```sh
PYTHONPATH=src .venv/bin/python -m archive_mcp survey runtime/archive.sqlite --max-chars 12000
```

使用返回的 `next_cursor` 继续。推荐项目或判断当前状态前，先用最新消息顺序读取相关对话，并检查其他对话是否有更新。调查结果只代表实际读到的内容，不代表整个历史都已覆盖。

## 配置刷新

创建 `runtime/sources.json`，只列出你希望定期读取的导出文件或文件夹：

```json
{
  "exports": [
    {"path": "/absolute/path/to/selected-export", "account": "personal"}
  ]
}
```

macOS/Linux：

```sh
PYTHONPATH=src .venv/bin/python -m archive_mcp refresh runtime/archive.sqlite runtime/sources.json
```

Windows PowerShell：

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
.\.venv\Scripts\python.exe -m archive_mcp refresh runtime\archive.sqlite runtime\sources.json
```

刷新会读取当前已有的源文件；它不会向服务商请求新的导出，不会安装后台监视器，也不保证删除输入文件后数据库中的记录自动消失。

## 导入本地编程会话

如果只想选择部分本地会话，可以在配置中指定提供商：

```json
{
  "exports": [],
  "local": {
    "account": "personal",
    "providers": ["codex", "claude-code"]
  }
}
```

常见位置：

| 提供商 | 默认位置 |
| --- | --- |
| codex | `$CODEX_HOME/sessions` 或 `~/.codex/sessions` |
| claude-code | `~/.claude/projects` |
| antigravity | `~/.gemini/antigravity/conversations` |
| qwen-code | `~/.qwen/projects` |

没有 `local` 配置时不会导入本地会话；空的 `providers` 列表表示不选择任何本地存储。未选中的存储不会被扫描。

一次性同步示例：

```sh
PYTHONPATH=src .venv/bin/python -m archive_mcp sync-local runtime/archive.sqlite --provider codex --provider claude-code --account personal
```

导入前请结束会话写入。特别是读取 Antigravity 的数据库前要关闭 Antigravity，否则无法保证数据库视图一致。源文件保持不变。

## 常用 Make 命令

在 macOS/Linux 的 POSIX shell 中可以使用：

| 命令 | 用途 |
| --- | --- |
| `make setup` | 创建目录、虚拟环境并安装依赖 |
| `make import` | 使用默认账号标签导入 `imports` 下的内容 |
| `make report` | 查看最近的导入报告 |
| `make refresh` | 读取 `runtime/sources.json` 并刷新 |
| `make check` | 检查档案完整性 |

Windows 请使用上面的 PowerShell 命令。

## 故障排查

- `FileNotFoundError`：检查输入文件、文件夹和数据库路径。
- `JSONDecodeError`：确认输入文件是有效 JSON，并且格式受支持。
- 搜索没有结果：先查看导入报告，减少关键词，并检查服务商、账号和日期筛选。
- 结果摘要可能被截断；通过 MCP 客户端读取完整消息页。
- 如果修改了数据库或筛选条件，重新开始分页或搜索。

更详细的技术说明请参阅 [MCP 工具文档](MCP_TOOLS.md)；贡献者测试请参阅 [开发检查](DEVELOPMENT.md)。
