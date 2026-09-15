# AI Pensieve MCP

搜索你导入的 AI 对话记录，并通过你常用的 MCP 客户端使用这些记录。

> **隐私：** 档案保存在本地，MCP 接口是只读的。读取到的文本可能会按照你所使用的 AI 客户端设置发送给对应的模型服务商。

支持导入 ChatGPT、Claude、Gemini、DeepSeek、Grok 以及部分编程工具的会话。NotebookLM 目前只支持笔记本元数据。

这是一个简明中文安装和使用手册。完整的英文文档请参阅项目中的 [README](README.md)、[AI 客户端设置](docs/AI_CLIENTS.md) 和 [用户指南](docs/USER_GUIDE.md)。

## 1. 安装

安装 [uv](https://docs.astral.sh/uv/getting-started/installation/) 后，一条命令打开桌面界面：

```sh
uvx ai-pensieve
```

也可以运行 `pipx install ai-pensieve`，然后运行 `pensieve`。
[MCP 命令和平台要求](docs/INSTALLATION.md)。下面仍提供源码安装方式。

从 [GitHub](https://github.com/AS-XS/AI-Pensieve-MCP) 下载 ZIP，解压后在终端进入项目文件夹。需要 Python 3.10 或更高版本，并且 SQLite 支持 FTS5。

macOS/Linux：

```sh
mkdir -p imports runtime
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Windows PowerShell：

```powershell
New-Item -ItemType Directory -Force imports, runtime | Out-Null
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 2. 导入历史记录

先按照[应用导出指南](docs/EXPORT_GUIDE.md)导出并解压文件，然后把想要导入的文件或文件夹放到一个选择目录中。不同账号请使用不同目录和账号标签。

macOS/Linux：

```sh
PYTHONPATH=src .venv/bin/python -m archive_mcp import-auto runtime/archive.sqlite imports/account-one --account account-one
PYTHONPATH=src .venv/bin/python -m archive_mcp check runtime/archive.sqlite
```

Windows PowerShell：

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
.\.venv\Scripts\python.exe -m archive_mcp import-auto runtime\archive.sqlite imports\account-one --account account-one
.\.venv\Scripts\python.exe -m archive_mcp check runtime\archive.sqlite
```

导入不会修改原始文件。成功的完整性检查会返回 `"ok": true`。重复导入相同内容不会创建重复的规范记录。

## 3. 连接和使用

请先阅读[中文 AI 客户端设置](docs/AI_CLIENTS.zh-CN.md)，再查看[中文用户指南](docs/USER_GUIDE.zh-CN.md)。连接完成后，可以尝试：

> 搜索我的档案中关于机器学习的讨论，并给出支持结论的来源对话和日期。

> 查找不同 AI 服务商对我的项目做过的讨论，并比较其中记录的决定。

MCP 服务搜索的是已经导入的本地快照。新的对话需要再次导入或刷新后才会出现。

也可以先运行合成演示：

```sh
PYTHONPATH=src .venv/bin/python -m archive_mcp.demo
```

演示只使用项目自带的合成数据，不读取你的个人导出文件。

项目还提供可选的桌面界面：请参阅 [GUI 文档](docs/GUI.md)。
