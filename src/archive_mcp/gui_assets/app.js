"use strict";
const $ = (id) => document.getElementById(id);
const state = {
  page: "door",
  selected: null,
  readerGeneration: 0,
  searchGeneration: 0,
  importing: false,
};
function el(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}
function ui(tag, text, className) {
  const node = el(tag, undefined, className);
  bindUI(node, text);
  return node;
}
function error(message = "") {
  const target = $("reader-dialog").open
    ? $("reader-dialog")
    : $("workbench").open
      ? $("workbench")
      : document.body;
  target.append($("error"));
  bindUI($("error"), message);
  $("error").hidden = !message;
}
async function api(name, ...args) {
  const response = await window.pywebview.api[name](...args);
  if (!response.ok) throw new Error(response.error);
  return response.data;
}
function guarded(fn) {
  return async (event) => {
    if (event) event.preventDefault();
    try {
      error();
      await fn(event);
    } catch (e) {
      error(e.message);
    }
  };
}
function show(page) {
  state.page = page;
  $("basin-menu").hidden = true;
  $("pensieve").setAttribute("aria-expanded", "false");
  document.body.dataset.scene = page === "search" ? "search" : "room";
  $("library-view").hidden = !["library", "search"].includes(page);
  $("import-view").hidden = page !== "import";
  $("connect-view").hidden = page !== "connect";
  $("workbench").dataset.mode = page;
  bindUI(
    $("page-name"),
    {
      library: "Your collected memories",
      import: "Choose a memory vessel",
      search: "Look into the waters",
      connect: "Connect to an AI",
    }[page],
  );
  bindUI(
    $("panel-eyebrow"),
    page === "import" ? "THE MEMORY RITUAL" : "THE MEMORY SHELF",
  );
  if (!$("workbench").open) $("workbench").showModal();
  $("workbench").querySelector(".workbench-surface").scrollTop = 0;
  if (page === "library") guarded(() => browse())();
  if (page === "connect") guarded(connectionConfig)();
  if (page === "search") {
    $("browse-more").hidden = true;
    $("query").focus();
  }
}
function options(id, values, placeholder) {
  const select = $(id),
    old = select.value;
  select.replaceChildren();
  if (placeholder) {
    const option = new Option("", "");
    bindUI(option, placeholder);
    select.append(option);
  }
  for (const [value, label] of values) {
    const option = new Option(label, value);
    if (id === "source-format") bindUI(option, label);
    select.append(option);
  }
  if ([...select.options].some((o) => o.value === old)) select.value = old;
}
async function refresh() {
  const data = await api("status");
  $("database-path").textContent = data.database;
  $("demo-note").hidden = !data.demo_sources;
  $("connect-ai").disabled = Boolean(data.demo_sources);
  if (data.demo_sources) {
    $("source-path").value = data.demo_sources;
    $("import-account").value = "synthetic-demo";
    $("quick-import").hidden = true;
  }
  $("inventory").replaceChildren();
  for (const [key, label] of [
    ["conversations", "Conversations"],
    ["messages", "Messages"],
    ["memories", "Saved context"],
  ]) {
    const row = el("div");
    row.append(ui("span", label));
    row.append(el("strong", data.totals[key].toLocaleString()));
    $("inventory").append(row);
  }
  options("source-format", Object.entries(data.formats));
  buildBottles(data.formats);
  options(
    "provider",
    [...new Set(data.sources.map((s) => s.provider))].map((p) => [p, p]),
    "All providers",
  );
  const accounts = [...new Set(data.sources.map((s) => s.account))];
  options(
    "account-filter",
    accounts.map((a) => [a, a]),
    "All accounts",
  );
  $("account-labels").replaceChildren(...accounts.map((a) => new Option(a, a)));
}
function date(value) {
  if (value === null || value === undefined)
    return translate("Date unavailable");
  const d = new Date(typeof value === "number" ? value * 1000 : value);
  return isNaN(d)
    ? translate("Date unavailable")
    : d.toLocaleString(language === "zh" ? "zh-CN" : "en-US", {
        dateStyle: "medium",
        timeStyle: "short",
      });
}
function dateNode(tag, value, className) {
  return ui(tag, () => date(value), className);
}
function attribution(group) {
  const row = el("div");
  row.append(
    providerBadge(group.provider),
    el("span", group.account, "source-account"),
  );
  return row;
}
async function search() {
  $("browse-more").hidden = true;
  const generation = ++state.searchGeneration;
  state.readerGeneration++;
  state.selected = null;
  $("results").replaceChildren();
  $("reader").replaceChildren(
    ui("div", "Choose a result to read its original messages.", "reader-empty"),
  );
  $("result-count").textContent = "—";
  bindUI($("search-note"), "Searching…");
  let result;
  try {
    result = await api(
      "search",
      $("query").value,
      $("provider").value,
      $("account-filter").value,
    );
  } catch (e) {
    if (generation !== state.searchGeneration) return;
    bindUI(
      $("search-note"),
      "Search could not finish. Adjust the query and try again.",
    );
    throw e;
  }
  if (generation !== state.searchGeneration) return;
  $("result-count").textContent = result.groups.length;
  bindUI(
    $("search-note"),
    result.groups.length
      ? result.candidate_limit_reached
        ? "Showing groups from the first 50 ranked matches. Narrow your search to find more."
        : `${result.candidates_examined} matching records, grouped by source.`
      : $("query").value.trim()
        ? "No matches. Try another keyword or fewer filters."
        : "Enter a keyword to search your imported history.",
  );
  renderGroups(result.groups);
}
function renderGroups(groups, append = false) {
  if (!append) $("results").replaceChildren();
  for (const group of groups) {
    const button = el("button", undefined, "result");
    button.append(
      attribution(group),
      group.title
        ? el("span", group.title, "result-title")
        : ui("span", "Untitled memory", "result-title"),
    );
    const first = group.matches?.[0];
    button.append(
      first?.snippet
        ? el("span", first.snippet, "result-snippet")
        : ui("span", "Saved in your collection", "result-snippet"),
      dateNode("span", first?.created_at ?? group.date, "result-date"),
    );
    button.addEventListener(
      "click",
      guarded(() => openGroup(group)),
    );
    $("results").append(button);
  }
}
let libraryOffset = null;
async function browse(append = false) {
  const generation = ++state.searchGeneration;
  const result = await api(
    "library",
    $("provider").value,
    $("account-filter").value,
    append ? libraryOffset : 0,
  );
  if (generation !== state.searchGeneration) return;
  if (!append) $("query").value = "";
  renderGroups(result.groups, append);
  libraryOffset = result.next_offset;
  $("browse-more").hidden = libraryOffset === null;
  $("result-count").textContent = $("results").children.length;
  bindUI(
    $("search-note"),
    result.groups.length
      ? "Collected memories · most recent first"
      : "The shelf is empty. Import a memory to begin.",
  );
}
function readerHeading(group, title, kind) {
  const header = el("div", undefined, "reader-heading");
  header.append(
    attribution(group),
    title ? el("h2", title) : ui("h2", "Untitled"),
    ui(
      "p",
      kind === "memory"
        ? "Saved context · separate from conversation messages"
        : "Original messages · all retained branches are shown",
      "hint",
    ),
    ui(
      "div",
      `Source ID: ${group.memory_id || group.conversation_id}`,
      "provenance",
    ),
  );
  $("reader").append(header);
}
async function openGroup(group) {
  if (!$("reader-dialog").open) $("reader-dialog").showModal();
  $("reader-surface").scrollTop = 0;
  state.selected = group;
  const generation = ++state.readerGeneration;
  $("reader").replaceChildren(ui("p", "Opening…", "hint"));
  if (group.group_type === "memory") {
    const page = await api(
      "memory",
      group.provider,
      group.account,
      group.memory_id,
      0,
    );
    if (generation !== state.readerGeneration) return;
    $("reader").replaceChildren();
    readerHeading(group, page.title, "memory");
    const body = el("div", page.text, "message-text");
    $("reader").append(dateNode("p", page.created_at, "hint"), body);
    memoryMore(group, page, body, generation);
  } else {
    const page = await api(
      "conversation",
      group.provider,
      group.account,
      group.conversation_id,
      0,
    );
    if (generation !== state.readerGeneration) return;
    $("reader").replaceChildren();
    readerHeading(group, page.conversation.title, "conversation");
    appendPage(group, page, generation);
  }
}
function memoryMore(group, page, body, generation) {
  if (page.next_offset === null) return;
  const more = ui("button", "Read more saved context", "load-more");
  $("reader").append(more);
  more.onclick = guarded(async () => {
    more.disabled = true;
    try {
      const next = await api(
        "memory",
        group.provider,
        group.account,
        group.memory_id,
        page.next_offset,
      );
      if (generation !== state.readerGeneration) return;
      body.textContent += next.text;
      more.remove();
      memoryMore(group, next, body, generation);
    } finally {
      more.disabled = false;
    }
  });
}
function appendPage(group, page, generation) {
  for (const message of page.messages) {
    const block = el("article", undefined, "message");
    const meta = el("div", undefined, "message-meta");
    meta.append(
      ui("span", message.role || "Unknown role", "message-role"),
      dateNode("span", message.created_at),
    );
    const body = el("div", message.text, "message-text");
    const ids = el("details");
    ids.append(
      ui("summary", "Message & branch IDs"),
      ui(
        "div",
        `Node: ${message.node_source_id}\nParent: ${message.parent_source_id || "Root"}\nMessage: ${message.message_source_id || "Unavailable"}`,
        "provenance",
      ),
    );
    block.append(meta, body, ids);
    $("reader").append(block);
    if (message.truncated)
      addMessageMore(
        group,
        message.node_source_id,
        4000,
        body,
        block,
        generation,
      );
  }
  if (page.next_offset !== null) {
    const more = ui("button", "Load next 20 messages", "load-more");
    $("reader").append(more);
    more.onclick = guarded(async () => {
      more.disabled = true;
      try {
        const next = await api(
          "conversation",
          group.provider,
          group.account,
          group.conversation_id,
          page.next_offset,
        );
        if (generation !== state.readerGeneration) return;
        more.remove();
        appendPage(group, next, generation);
      } finally {
        more.disabled = false;
      }
    });
  }
}
function addMessageMore(group, nodeId, offset, body, block, generation) {
  const more = ui("button", "Read more of this message", "load-more");
  block.append(more);
  more.onclick = guarded(async () => {
    more.disabled = true;
    try {
      const page = await api(
        "message",
        group.provider,
        group.account,
        group.conversation_id,
        nodeId,
        offset,
      );
      if (generation !== state.readerGeneration) return;
      body.textContent += page.text;
      more.remove();
      if (page.next_offset !== null)
        addMessageMore(
          group,
          nodeId,
          page.next_offset,
          body,
          block,
          generation,
        );
    } finally {
      more.disabled = false;
    }
  });
}
let previewGeneration = 0;
async function preview() {
  $("import-form").classList.remove("source-ready");
  const generation = ++previewGeneration;
  const data = await api(
    "preview",
    $("source-path").value,
    $("source-format").value,
  );
  if (generation !== previewGeneration) return;
  $("import-form").classList.toggle("source-ready", data.files > 0);
  bindUI(
    $("preview"),
    `${data.files} supported file${data.files === 1 ? "" : "s"} selected\n${Object.entries(
      data.formats,
    )
      .map(([name, n]) => `${name}: ${n}`)
      .join(
        " · ",
      )}\n${data.unrecognized} unrecognized candidates · ${data.other_formats} files in other formats\n${data.note}`,
  );
}
async function choose(folder) {
  const path = await api("choose", folder);
  if (path) {
    $("source-path").value = path;
    await preview();
  }
}
function importResult(result) {
  const section = $("import-result");
  section.hidden = false;
  section.replaceChildren(
    ui(
      "h2",
      result.error
        ? "Import stopped"
        : result.total
          ? "Memories received."
          : "No supported files selected.",
    ),
  );
  section.append(
    ui(
      "p",
      `${result.completed} of ${result.total} selected files committed. Earlier successful files remain if a later file fails.`,
    ),
  );
  if (result.error) section.append(ui("p", result.error, "error"));
  const table = el("table"),
    head = el("tr");
  for (const label of [
    "Records",
    "New",
    "Updated",
    "Unchanged",
    "Protected",
    "Removed",
  ])
    head.append(ui("th", label));
  table.append(head);
  for (const [kind, counts] of Object.entries(result.changes)) {
    const row = el("tr");
    row.append(ui("th", kind === "nodes" ? "Message nodes" : kind));
    for (const key of ["new", "updated", "unchanged", "protected", "removed"])
      row.append(el("td", counts[key]));
    table.append(row);
  }
  section.append(
    table,
    ui(
      "p",
      "Counts sum committed files; overlapping files can count the same identity more than once.",
      "hint",
    ),
  );
  const warnings = Object.entries(result.warnings).map(
    ([key, n]) => `${key.replaceAll("_", " ")}: ${n}`,
  );
  if (warnings.length || result.other_formats)
    section.append(
      ui(
        "p",
        [
          ...warnings,
          `${result.other_formats} files skipped by format selection`,
        ].join(" · "),
        "hint",
      ),
    );
  const back = ui("button", "Search your library →", "text-button");
  back.onclick = () => {
    show("search");
    $("query").focus();
  };
  section.append(back);
}
async function importSources(local = false) {
  if (state.importing) return;
  const path = $("source-path").value,
    kind = $("source-format").value,
    account = $("import-account").value.trim();
  local = local || (!path.trim() && kind === "auto");
  if ((!local && !path.trim()) || !account)
    throw new Error("Choose a source and enter an account label.");
  if (local) {
    $("source-format").value = "auto";
    for (const bottle of $("bottle-rack").children)
      bottle.setAttribute(
        "aria-pressed",
        String(bottle.dataset.provider === "auto"),
      );
    bindUI($("selected-format"), "Local sessions · automatic discovery");
  }
  state.importing = true;
  $("close-workbench").disabled = true;
  error();
  $("import-result").hidden = true;
  $("progress").hidden = false;
  const controls = [
    ...$("import-form").querySelectorAll("button,input,select"),
  ];
  controls.forEach((n) => (n.disabled = true));
  const progress = $("progress").querySelector("progress"),
    text = $("progress").querySelector("span");
  progress.removeAttribute("value");
  bindUI(
    text,
    local ? "Finding supported local sessions…" : "Inspecting selected files…",
  );
  let polling = false;
  const timer = setInterval(async () => {
    if (polling) return;
    polling = true;
    try {
      const p = await api("progress");
      if (p.total !== null && p.total > 0) {
        progress.max = p.total;
        progress.value = p.completed;
        bindUI(
          text,
          `${p.completed} of ${p.total} files committed. Keep this window open until the import finishes.`,
        );
      }
    } catch (e) {
      /* The operation itself reports its failure. */
    } finally {
      polling = false;
    }
  }, 350);
  try {
    const result = local
      ? await api("import_local", account)
      : await api("import_sources", path, kind, account);
    if (local) {
      bindUI(
        $("preview"),
        result.total
          ? `${result.total} local session files found`
          : "No supported local sessions found in the known folders. Choose a custom folder for other locations.",
      );
      $("import-form").classList.toggle("source-ready", result.total > 0);
    }
    if (result.completed > 0) await pourMemory();
    importResult(result);
    state.readerGeneration++;
    state.searchGeneration++;
    $("results").replaceChildren();
    $("reader").replaceChildren(
      ui(
        "div",
        "The archive has changed. Search again to read current results.",
        "reader-empty",
      ),
    );
    $("result-count").textContent = "—";
    bindUI($("search-note"), "Search again after importing.");
    await refresh();
    $("import-result").scrollIntoView({ block: "center" });
  } finally {
    clearInterval(timer);
    state.importing = false;
    $("close-workbench").disabled = false;
    controls.forEach((n) => (n.disabled = false));
    $("progress").hidden = true;
  }
}
let connectionGeneration = 0;
async function connectionConfig() {
  const generation = ++connectionGeneration;
  const client = $("connection-client").value;
  $("copy-connection").disabled = true;
  $("connection-config").value = "";
  bindUI($("connection-status"), "");
  const result = await api("connection_config", client);
  if (generation !== connectionGeneration) return;
  $("connection-config").value = result.configuration;
  bindUI($("connection-launcher"), result.launcher);
  bindUI($("connection-instructions"), {
    codex: "Add this entry to ~/.codex/config.toml (or your CODEX_HOME config.toml). Update an existing ai-pensieve-mcp entry instead of adding a duplicate.",
    "claude-desktop": "In Claude Desktop, open Settings → Developer → Edit Config. Add this server inside mcpServers in claude_desktop_config.json.",
    cursor: "Add this server inside mcpServers in ~/.cursor/mcp.json for your personal configuration.",
    generic: "Use these command, arguments and environment values in a client that supports local STDIO. Its configuration format may differ.",
  }[client]);
  bindUI($("connection-evidence"), client === "codex"
    ? "Codex CLI was tested on macOS with synthetic data. Desktop setup remains unverified."
    : client === "generic" ? "Client integration unverified."
    : "Official configuration format checked; integration with this archive is not yet tested in this client.");
  $("copy-connection").disabled = false;
}
$("connect-ai").onclick = () => show("connect");
$("connection-client").onchange = guarded(connectionConfig);
$("copy-connection").onclick = guarded(async () => {
  const field = $("connection-config");
  try {
    await navigator.clipboard.writeText(field.value);
  } catch (_) {
    field.focus();
    field.select();
    if (!document.execCommand("copy")) {
      bindUI($("connection-status"), "Select the configuration and copy it with your keyboard.");
      return;
    }
  }
  bindUI($("connection-status"), "Configuration copied. Paste it into your client's settings.");
});
$("browse-library").onclick = guarded(() => browse());
$("browse-more").onclick = guarded(() => browse(true));
$("empty-import").onclick = () => show("import");
$("search-form").onsubmit = guarded(search);
$("choose-folder").onclick = guarded(() => choose(true));
$("choose-file").onclick = guarded(() => choose(false));
$("preview-button").onclick = guarded(preview);
$("source-format").onchange = () => {
  $("import-form").classList.remove("source-ready");
  bindUI($("preview"), "Selection changed. Check it again before importing.");
  previewGeneration++;
};
$("source-path").oninput = () => {
  $("import-form").classList.remove("source-ready");
  bindUI($("preview"), "Selection changed. Check it again before importing.");
  previewGeneration++;
};
$("import-form").onsubmit = guarded(() => importSources());
$("import-local").onclick = guarded(() => importSources(true));
window.addEventListener("pywebviewready", guarded(refresh));

for (const id of ["provider", "account-filter"])
  $(id).onchange = guarded(() =>
    state.page === "library" && !$("query").value.trim() ? browse() : search(),
  );
$("close-reader").onclick = () => $("reader-dialog").close();
$("reader-dialog").addEventListener("close", () => {
  state.readerGeneration++;
});
