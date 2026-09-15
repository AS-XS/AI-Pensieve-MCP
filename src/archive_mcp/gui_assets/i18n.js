"use strict";
let language = "en";
const chinese = {
  "Copy the configuration below into your AI client's settings. This window does not set up the client automatically.": "请将以下配置复制到 AI 客户端的设置中。本窗口不会自动设置客户端。",
  "Connect to an AI": "连接 AI 客户端",
  "AI client": "AI 客户端",
  "Other local STDIO client": "其他本地 STDIO 客户端",
  "Your AI client can read this archive. Retrieved excerpts may be sent to its model provider.": "AI 客户端可以读取此档案。检索到的片段可能会发送给其模型服务商。",
  "Configuration for this archive": "此档案的连接配置",
  "Copy configuration": "复制配置",
  "Merge this entry with your existing settings, then restart the client. Ask it to check archive status.": "将此条目合并到已有设置，然后重启客户端。请它检查档案状态。",
  "Web and mobile chat apps cannot connect directly to this local server.": "网页和手机聊天应用无法直接连接此本地服务。",
  "Uses uvx. Keep uv installed.": "使用 uvx 启动，请保留 uv 安装。",
  "Uses this installation. Copy a new configuration if you move or reinstall it.": "使用当前安装。移动或重新安装后，请重新复制配置。",
  "Add this entry to ~/.codex/config.toml (or your CODEX_HOME config.toml). Update an existing ai-pensieve-mcp entry instead of adding a duplicate.": "将此条目添加到 ~/.codex/config.toml（或 CODEX_HOME 下的 config.toml）。如已有 ai-pensieve-mcp 条目，请更新它。",
  "In Claude Desktop, open Settings → Developer → Edit Config. Add this server inside mcpServers in claude_desktop_config.json.": "在 Claude Desktop 中打开 Settings → Developer → Edit Config，将此服务添加到 claude_desktop_config.json 的 mcpServers 中。",
  "Add this server inside mcpServers in ~/.cursor/mcp.json for your personal configuration.": "将此服务添加到个人配置 ~/.cursor/mcp.json 的 mcpServers 中。",
  "Use these command, arguments and environment values in a client that supports local STDIO. Its configuration format may differ.": "在支持本地 STDIO 的客户端中填写这些命令、参数和环境变量。具体配置格式可能不同。",
  "Codex CLI was tested on macOS with synthetic data. Desktop setup remains unverified.": "已在 macOS 上用合成数据测试 Codex CLI。桌面客户端设置仍未验证。",
  "Client integration unverified.": "此客户端集成尚未验证。",
  "Official configuration format checked; integration with this archive is not yet tested in this client.": "已核对官方配置格式；尚未在此客户端测试本档案的集成。",
  "Select the configuration and copy it with your keyboard.": "请选中配置文本并使用键盘复制。",
  "Configuration copied. Paste it into your client's settings.": "配置已复制，请粘贴到客户端设置。",
  "Demo room: invented conversations only. Import the examples, then search for garden or research. This archive is removed when the window closes.": "演示密室：仅包含虚构对话。导入示例后搜索 garden 或 research。关闭窗口后，此档案会被清理。",
  "← Return to chamber": "← 返回密室",
  "The Pensieve chamber": "冥想盆密室",
  "Touch the Pensieve": "触碰冥想盆",
  "The Pensieve": "冥想盆",
  "Open the memory bottle shelf — library": "打开记忆瓶架——记忆库",
  "Open the prophecy orb shelf — sources": "打开预言球架——记忆来源",
  "The memory shelf": "记忆瓶架",
  "The collected sources": "收集的记忆来源",
  "What memory will you stir?": "你想唤起哪段记忆？",
  "Import a memory": "导入记忆",
  "Search the waters": "探寻记忆之水",
  "Touch the Pensieve. The shelves hold your collected memories.":
    "触碰冥想盆。两侧的架子收藏着你的记忆。",
  "← The doorway": "← 返回门前",
  "The closed door": "紧闭的木门",
  "Open the wooden door": "推开木门",
  "A memory waits within.": "一段记忆，静候门后。",
  "Touch the door to enter": "轻触木门，步入密室",
  "Enter without the transition": "跳过开门动画",
  "Still the magic": "暂停魔法动画",
  "Wake the magic": "唤醒魔法动画",
  "THE MEMORY SHELF": "记忆之架",
  "Your collected memories": "收藏的记忆",
  "Return to the chamber ↗": "返回密室 ↗",
  "Return to the chamber": "返回密室",
  "Browse the collection": "浏览记忆库",
  "Add a memory": "添加记忆",
  "Search memories": "搜索记忆",
  "What do you wish to remember?": "你想回忆起什么？",
  Search: "搜索",
  Provider: "来源平台",
  Account: "账户",
  "All providers": "所有平台",
  "All accounts": "所有账户",
  "Ask the waters for a word, an idea, a memory.":
    "用一个词、一个想法，唤起水中的记忆。",
  "Memory results": "记忆搜索结果",
  "More memories": "更多记忆",
  "Selected import format": "所选导入格式",
  "Choose a provider memory bottle": "选择平台记忆瓶",
  "The unmarked bottle · detect supported files":
    "无标记的瓶子 · 自动识别支持的文件",
  "Choose where this memory comes from": "选择记忆的来源位置",
  "A file or folder on this computer": "本机文件或文件夹",
  "Choose folder": "选择文件夹",
  File: "选择文件",
  "Account label": "账户标签",
  "Inspect selection": "检查所选来源",
  "Use the same account label for later exports. Extract ZIPs first; close ZCode before importing its store.":
    "后续导出请使用相同账户标签。请先解压 ZIP；导入 ZCode 数据库前请关闭 ZCode。",
  "Choose a bottle, then a source. Your original files stay where they are.":
    "选择记忆瓶，再选择来源。原始文件会保留在原处。",
  "Pour into the Pensieve": "倒入冥想盆",
  "Stored only on this computer": "仅存储在这台电脑上",
  "Original memory": "原始记忆",
  "← Back to the memories": "← 返回记忆列表",
  "Conversation reader": "对话阅读器",
  "Find & import local sessions": "一键查找并导入本地会话",
  "One click: Codex, Claude Code, Qwen Code, Antigravity and ZCode in their known folders. Close native apps first. Uses the account label below; website exports still need a folder.":
    "一键查找已知目录中的 Codex、Claude Code、Qwen Code、Antigravity 和 ZCode 会话。请先关闭相关应用。使用下方账户标签；网页聊天导出仍需选择文件夹。",
  "Choose a memory vessel": "选择记忆之瓶",
  "Look into the waters": "凝视记忆之水",
  "THE MEMORY RITUAL": "记忆仪式",
  Conversations: "对话",
  Messages: "消息",
  "Saved context": "已保存的上下文",
  "Date unavailable": "日期未知",
  "Choose a result to read its original messages.":
    "选择一条结果，阅读原始消息。",
  "Searching…": "正在搜索…",
  "Search could not finish. Adjust the query and try again.":
    "搜索未完成。请调整关键词后重试。",
  "Showing groups from the first 50 ranked matches. Narrow your search to find more.":
    "当前按前 50 条相关匹配分组显示。请缩小搜索范围以查找更多内容。",
  "No matches. Try another keyword or fewer filters.":
    "没有匹配结果。请尝试其他关键词或减少筛选条件。",
  "Enter a keyword to search your imported history.":
    "输入关键词，搜索已导入的历史记录。",
  "Untitled memory": "无标题记忆",
  "Saved in your collection": "已收藏到记忆库",
  "Collected memories · most recent first": "收藏的记忆 · 按时间倒序",
  "The shelf is empty. Import a memory to begin.":
    "架子还是空的。先导入一段记忆吧。",
  Untitled: "无标题",
  "Saved context · separate from conversation messages":
    "已保存的上下文 · 与对话消息分开",
  "Original messages · all retained branches are shown":
    "原始消息 · 显示所有保留的分支",
  "Opening…": "正在打开…",
  "Read more saved context": "继续阅读上下文",
  "Unknown role": "未知角色",
  "Message & branch IDs": "消息与分支标识",
  "Load next 20 messages": "加载后续 20 条消息",
  "Read more of this message": "继续阅读此消息",
  "Import stopped": "导入已停止",
  "Memories received.": "记忆已收录。",
  "No supported files selected.": "未找到支持的文件。",
  Records: "记录",
  New: "新增",
  Updated: "更新",
  Unchanged: "未变化",
  Protected: "已保护",
  Removed: "已移除",
  "Message nodes": "消息节点",
  conversations: "对话",
  memories: "记忆",
  "Counts sum committed files; overlapping files can count the same identity more than once.":
    "计数汇总已提交的文件；文件有重叠时，同一条记录可能被多次计入。",
  "Search your library →": "搜索记忆库 →",
  "Choose a source and enter an account label.": "请选择来源并填写账户标签。",
  "Inspecting selected files…": "正在检查所选文件…",
  "Finding supported local sessions…": "正在查找支持的本地会话…",
  "Local sessions · automatic discovery": "本地会话 · 自动发现",
  "No supported local sessions found in the known folders. Choose a custom folder for other locations.":
    "已知目录中未找到支持的本地会话。若保存在其他位置，请手动选择文件夹。",
  "The archive has changed. Search again to read current results.":
    "记忆库已更新。请重新搜索以读取最新结果。",
  "Search again after importing.": "导入完成，请重新搜索。",
  "Selection changed. Check it again before importing.":
    "来源已更改，请在导入前重新检查。",
  "Your memory has reached the Pensieve.": "你的记忆已汇入冥想盆。",
  Unmarked: "无标记",
  "Auto-detect all": "全部自动识别",
  "Auto-detect all supported formats": "自动识别所有支持的格式",
  "Unmarked bottle: auto-detect all supported formats":
    "无标记记忆瓶：自动识别所有支持的格式",
  "Generic saved context": "通用已保存上下文",
  export: "导出文件",
  "projects & saved context": "项目与已保存上下文",
  "activity HTML (replaces activity)": "活动 HTML（替换活动记录）",
  "metadata only": "仅元数据",
  "local session": "本地会话",
  "session/export": "会话／导出",
  "JSON export": "JSON 导出",
  "observed local store": "已验证版本的本地存储",
  "closed SQLite store": "已关闭的 SQLite 数据库",
  user: "用户",
  assistant: "助手",
  system: "系统",
  developer: "开发者",
  tool: "工具",
  "Only supported JSON, JSONL, HTML and native-store candidates are inspected. Extract ZIPs first.":
    "仅检查支持的 JSON、JSONL、HTML 和本地数据库候选文件。请先解压 ZIP。",
  "That source no longer exists. Choose an existing file or folder.":
    "来源已不存在，请选择有效的文件或文件夹。",
  "The operation could not finish. For search, check the FTS expression; for imports, check whether another process is writing the archive.":
    "操作未完成。搜索时请检查 FTS 表达式；导入时请检查是否有其他进程正在写入记忆库。",
};
function translate(value) {
  const text = String(value ?? "");
  if (language !== "zh") return text;
  if (chinese[text]) return chinese[text];
  const patterns = [
    [
      /^(\d+) matching records, grouped by source\.$/,
      (_, n) => `${n} 条匹配记录，按来源分组。`,
    ],
    [/^(\d+) supported files? selected$/, (_, n) => `已选择 ${n} 个支持的文件`],
    [
      /^(\d+) unrecognized candidates · (\d+) files in other formats$/,
      (_, n, m) => `${n} 个未识别候选文件 · ${m} 个其他格式文件`,
    ],
    [
      /^(\d+) of (\d+) selected files committed\. Earlier successful files remain if a later file fails\.$/,
      (_, n, m) =>
        `${m} 个所选文件中已有 ${n} 个提交成功。后续文件失败时，之前成功的文件仍会保留。`,
    ],
    [
      /^(\d+) of (\d+) files committed\. Keep this window open until the import finishes\.$/,
      (_, n, m) =>
        `${m} 个文件中已有 ${n} 个提交成功。导入完成前请保持窗口打开。`,
    ],
    [/^(\d+) local session files found$/, (_, n) => `找到 ${n} 个本地会话文件`],
    [
      /^(\d+) files skipped by format selection$/,
      (_, n) => `按格式筛选跳过 ${n} 个文件`,
    ],
    [/^Source ID: (.*)$/, (_, id) => `来源标识：${id}`],
    [/^Node: (.*)$/, (_, id) => `节点：${id}`],
    [/^Parent: (.*)$/, (_, id) => `父节点：${id === "Root" ? "根节点" : id}`],
    [
      /^Message: (.*)$/,
      (_, id) => `消息：${id === "Unavailable" ? "不可用" : id}`,
    ],
    [
      /^Operation failed \(([^)]+)\)\. Check the selected input and try again\.$/,
      (_, kind) => `操作失败（${kind}）。请检查所选输入后重试。`,
    ],
    [
      /^Import stopped \(([^)]+)\)\. Check the selected export format; close native apps before importing their stores\.$/,
      (_, kind) =>
        `导入已停止（${kind}）。请检查导出格式；导入本地数据库前请关闭相关应用。`,
    ],
  ];
  for (const [pattern, replace] of patterns)
    if (pattern.test(text)) return text.replace(pattern, replace);
  if (text.includes("\n")) return text.split("\n").map(translate).join("\n");
  if (text.includes(" · ")) return text.split(" · ").map(translate).join(" · ");
  return text;
}
const uiBindings = new Map(),
  attributeBindings = new Map();
let cleanupQueued = false;
function pruneBindings() {
  if (cleanupQueued) return;
  cleanupQueued = true;
  queueMicrotask(() => {
    for (const node of uiBindings.keys())
      if (!node.isConnected) uiBindings.delete(node);
    for (const node of attributeBindings.keys())
      if (!node.isConnected) attributeBindings.delete(node);
    cleanupQueued = false;
  });
}
function bindUI(node, source) {
  pruneBindings();
  uiBindings.set(node, source);
  node.textContent = translate(
    typeof source === "function" ? source() : source,
  );
}
function bindAttribute(node, attribute, source) {
  pruneBindings();
  if (!attributeBindings.has(node)) attributeBindings.set(node, {});
  attributeBindings.get(node)[attribute] = source;
  node.setAttribute(attribute, translate(source));
}
// Capture only the original static UI, before any archive records are rendered.
const staticWalker = document.createTreeWalker(
  document.body,
  NodeFilter.SHOW_TEXT,
);
let staticText;
while ((staticText = staticWalker.nextNode())) {
  if (staticText.parentElement.closest("script,style")) continue;
  const source = staticText.textContent.trim().replace(/\s+/g, " ");
  if (source) uiBindings.set(staticText, source);
}
for (const node of document.querySelectorAll("[aria-label],[placeholder]")) {
  for (const attribute of ["aria-label", "placeholder"])
    if (node.hasAttribute(attribute))
      bindAttribute(node, attribute, node.getAttribute(attribute));
}
function changeLanguage() {
  language = language === "en" ? "zh" : "en";
  document.documentElement.lang = language === "zh" ? "zh-CN" : "en";
  for (const [node, source] of uiBindings) {
    if (!node.isConnected) {
      uiBindings.delete(node);
      continue;
    }
    node.textContent = translate(
      typeof source === "function" ? source() : source,
    );
  }
  for (const [node, attributes] of attributeBindings) {
    if (!node.isConnected) {
      attributeBindings.delete(node);
      continue;
    }
    for (const [attribute, source] of Object.entries(attributes))
      node.setAttribute(attribute, translate(source));
  }
  const control = document.getElementById("language-toggle");
  control.textContent = language === "zh" ? "English" : "中文";
  control.setAttribute(
    "aria-label",
    language === "zh" ? "Switch to English" : "切换为中文",
  );
}
document.getElementById("language-toggle").onclick = changeLanguage;
function placeLanguageControl() {
  const reader = document.getElementById("reader-dialog");
  const panel = document.getElementById("workbench");
  const target = reader.open ? reader : panel.open ? panel : document.body;
  target.append(document.getElementById("language-toggle"));
  (reader.open ? reader : panel).append(
    document.getElementById("close-workbench"),
  );
}
const dialogObserver = new MutationObserver(placeLanguageControl);
for (const id of ["workbench", "reader-dialog"])
  dialogObserver.observe(document.getElementById(id), {
    attributes: true,
    attributeFilter: ["open"],
  });
