# AI Pensieve MCP

搜索本地导入的 AI 对话记录，可通过魔法风格的桌面界面或 MCP 客户端使用。

English：[README](README.md) · [AI 客户端设置](docs/AI_CLIENTS.md) · [用户指南](docs/USER_GUIDE.md)

> **隐私：** 档案保存在本机，MCP 工具是只读的。读取到的片段可能会发送给你连接的 AI 服务商。
> [数据处理说明](docs/privacy/README.md)

## 安装

安装 [uv](https://docs.astral.sh/uv/getting-started/installation/) 后运行桌面界面：

```sh
uvx ai-pensieve
```

或者使用持久命令：

```sh
pipx install ai-pensieve
pensieve
```

只运行只读 MCP 服务时：

```sh
uvx ai-pensieve-mcp /absolute/path/to/archive.sqlite
```

请参阅[独立安装指南](docs/INSTALLATION.md)，了解客户端设置、平台要求、档案路径和源码安装。

## 使用桌面界面

1. 打开木门，触碰 Pensieve。
2. 选择“导入记忆”，再选择服务商瓶子、“未标记”自动识别，或“查找并导入本地会话”。
3. 选择导出文件或文件夹，检查选择结果，然后倒入盆中。原始文件不会被修改。
4. 选择“搜索水面”，输入关键词，再点击烟雾结果阅读原始线程。

支持导入 ChatGPT、Claude、Gemini、DeepSeek、Grok 以及部分编程工具会话。NotebookLM 目前仅导入笔记本元数据。
请查看[完整兼容性矩阵](docs/COMPATIBILITY.md)和[导出指南](docs/EXPORT_GUIDE.md)。

## 连接 AI 客户端

先导入档案，再阅读 [AI 客户端设置](docs/AI_CLIENTS.zh-CN.md) 和[客户端验证状态](docs/COMPATIBILITY.md#mcp-clients)。可以尝试：

> 搜索我的档案中关于机器学习的讨论，并给出支持结论的来源对话和日期。

> 查找不同 AI 服务商对我的项目做过的讨论，并比较其中记录的决定。

更多[示例提示词和工具说明](docs/EXAMPLE_PROMPTS.md)。档案是本地快照；新对话需要再次导入或刷新。
命令行导入、自定义来源文件夹、版本和去重规则请参阅[用户指南](docs/USER_GUIDE.zh-CN.md)。

项目采用 [Apache License 2.0](LICENSE)。

<!-- mcp-name: io.github.AS-XS/ai-pensieve-mcp -->
