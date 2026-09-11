# Compatibility and Import Roadmap

AI Pensieve MCP has two independent kinds of compatibility:

- **MCP client compatibility:** an AI application can search the existing
  archive by launching its local STDIO MCP server.
- **Import compatibility:** the archive can read that application's exported or
  local session history and add it to SQLite.

Supporting one does not imply the other. A model name is also not necessarily a
client: DeepSeek and Grok models can run inside several harnesses, while
DeepSeek Harness and Grok Build have their own session formats.

Non-OpenAI client references were rechecked on 2026-09-10; the OpenAI reference
was rechecked alongside the CLI integration test on 2026-09-10. Status has a specific meaning:

- **Tested:** this archive was exercised through the named client, with scope
  and date recorded. A generic SDK test does not qualify a third-party app.
- **Documented / untested:** official documentation supports the configuration,
  but this archive's integration has not been verified in that app/version.
- **Not supported:** this project provides no implementation for that connection
  or import format. A roadmap entry does not change this status.
- **Unverified:** insufficient evidence; no working setup is claimed.

Import adapters have synthetic tests for observed structures. Real-export
checks below are historical local evidence, not fresh downloads or validation
of every current export variant.

## MCP clients

| Client/surface | Archive integration evidence | Setup and official contract |
| --- | --- | --- |
| Bundled SDK STDIO demo | Current 12-tool demo tested locally on macOS/Python 3.13, 2026-09-11; previous 11-tool revision passed Ubuntu/Windows CI on Python 3.10/3.13 | [Demo scope](DEMO.md), [CI evidence](CLIENT_VERIFICATION.md#github-ci) |
| Codex CLI | Tested: 0.142.2 on macOS 26.6.2, 2026-09-10; temporary configuration, four explicit retrieval calls on synthetic data | [Verification](CLIENT_VERIFICATION.md#codex-cli), [setup](AI_CLIENTS.md#codex-cli-and-desktop), [official](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) |
| Codex-compatible desktop | Documented / current app integration unverified | [Setup](AI_CLIENTS.md#codex-cli-and-desktop), [official](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) |
| Codex IDE extension | Documented / untested | [Setup](AI_CLIENTS.md#codex-cli-and-desktop), [official](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) |
| Claude Code | Documented / untested; earlier CLI syntax check is not an integration test | [Setup](AI_CLIENTS.md#claude-code), [official](https://code.claude.com/docs/en/mcp) |
| Claude Desktop | Documented / untested | [Setup](AI_CLIENTS.md#claude-desktop), [official manual setup](https://modelcontextprotocol.io/docs/develop/connect-local-servers) |
| Antigravity CLI/IDE | Historical local tool calls on 2026-09-04; client version/surface unrecorded, current compatibility unverified | [Setup](AI_CLIENTS.md#antigravity-cli-and-ide), [official](https://antigravity.google/docs/mcp) |
| Cursor local client | Documented / untested | [Setup](AI_CLIENTS.md#cursor), [official](https://prod.cursor.com/docs/mcp) |
| Gemini CLI | Documented / untested | [Setup](AI_CLIENTS.md#gemini-cli), [official](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/tutorials/mcp-setup.md) |
| GitHub Copilot CLI | Documented / untested | [Setup](AI_CLIENTS.md#github-copilot-cli), [official](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers) |
| Grok Build | Documented / untested | [Setup](AI_CLIENTS.md#grok-build), [official](https://docs.x.ai/build/features/mcp-servers) |
| OpenCode v2 | Documented / untested; example is v2-specific | [Setup](AI_CLIENTS.md#opencode), [official](https://opencode.ai/v2/docs/mcp-servers) |
| Cline CLI/IDE | Documented / untested in either surface | [Setup](AI_CLIENTS.md#cline-roo-code-and-windsurf), [official](https://docs.cline.bot/mcp/mcp-overview) |
| Roo Code extension | Documented / untested | [Setup](AI_CLIENTS.md#cline-roo-code-and-windsurf), [official](https://docs.roocode.com/features/mcp/using-mcp-in-roo) |
| Windsurf / Devin Desktop Cascade | Documented / untested; current reference redirects to Devin Desktop | [Setup](AI_CLIENTS.md#cline-roo-code-and-windsurf), [official](https://docs.devin.ai/desktop/cascade/mcp) |
| Zed | Documented / untested | [Setup](AI_CLIENTS.md#zed), [official](https://zed.dev/docs/ai/mcp) |
| Qwen Code | Documented / untested | [Setup](AI_CLIENTS.md#qwen-code), [official](https://qwenlm.github.io/qwen-code-docs/en/users/features/mcp/) |
| DeepSeek Harness with MCP client plugin | Documented / untested; not DeepSeek Chat | [Setup](AI_CLIENTS.md#deepseek-harness), [official](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/mcp/mcp-client/README.md) |
| Continue Agent mode | Documented / untested; Chat/Plan modes do not expose MCP tools per the cited guide | [Setup](AI_CLIENTS.md#continue), [official](https://docs.continue.dev/customize/deep-dives/mcp) |

These documented configurations launch a local process when supported by the
installed client. They are not a blanket tested-client list. Model choice does
not supply a missing client transport, and a client's tool-calling behavior
still needs evaluation. No Windows or Linux third-party integration is certified
by the macOS SDK demo. Version-specific setups not covered here are unverified.

## Connections not supported by this project

This server exposes local STDIO only: no hosted MCP URL, HTTP/SSE listener,
browser extension, mobile companion, or remote bridge. The following statuses
refer to direct connection to this implementation, not every capability a
vendor may offer through other integrations.

| Surface or connection | Status | Reason |
| --- | --- | --- |
| ChatGPT web/mobile | Not supported directly | No remote endpoint or project-provided local bridge |
| Claude web/mobile | Not supported directly | Claude Desktop/Code local setup does not register this server with web/mobile |
| Gemini Apps web/mobile | Not supported directly | Gemini CLI instructions do not apply to Gemini Apps |
| DeepSeek Chat web/mobile | Not supported directly | DeepSeek Harness plugin instructions do not apply to the chat app |
| Grok Chat web/mobile | Not supported directly | Grok Build configuration does not apply to the chat app |
| NotebookLM | Not supported as a client by this project | No archive connection integration is provided |
| Microsoft Copilot consumer chat, Perplexity chat, Mistral web chat | Not supported directly | No connection integration for this local server is provided |
| Remote HTTP/SSE-only MCP connection, including cloud agents expecting a URL | Not supported | This server provides no URL transport |
| Continue outside Agent mode | Not supported by the documented setup | The linked Continue guide limits MCP to Agent mode |

Other clients and modes are **unverified**, not automatically supported because
they advertise MCP. Any future bridge needs its own implementation and data-flow
review. Export support below does not enable live access from the exporting app.

## Implemented import sources

See [export instructions](EXPORT_GUIDE.md) for downloads and file selection.

| Source format | Scope | Confidence |
| --- | --- | --- |
| ChatGPT export | Conversation trees and string content parts, including non-dialogue roles | Verified with a real export and synthetic tests |
| Claude export | Conversations, projects, documents, and memories | Verified with a real export and synthetic tests |
| Gemini Takeout | English activity HTML with CST timestamps (UTC−06:00), prompts/responses in inferred sessions | Verified with the observed export and synthetic tests; other locales/timezones unsupported |
| NotebookLM export | Notebook container metadata only | Verified with a real export and synthetic tests |
| DeepSeek chat export | Conversation trees and visible dialogue | Verified with the observed export and synthetic tests |
| Grok chat export | Conversation trees and visible dialogue | Verified with the observed xAI export and synthetic tests |
| Codex local sessions | User dialogue and final answers; identified approval-review sessions are excluded | Verified with native local sessions and synthetic tests |
| Claude Code local sessions | User dialogue and final answers | Verified with native local sessions and synthetic tests |
| Antigravity local sessions | Completed visible dialogue | Verified with the native local database and synthetic tests |
| OpenCode JSON export | User dialogue and visible assistant text | Verified against the official export contract and synthetic tests |
| Qwen Code JSON/JSONL export and native session | User dialogue and visible assistant text | Verified against the official export implementation and synthetic tests |
| Z.ai ZCode native SQLite | Visible user prompts and assistant text | Observed ZCode 3.11.2 on macOS, one local session, plus synthetic tests; closed database only |

## Importer evidence and custom locations

Not every importer comes from an official storage specification. Codex,
Claude Code, Antigravity, and ZCode native readers are grounded in observed
local stores and synthetic tests. OpenCode and Qwen Code exports were checked
against official export implementations/contracts and synthetic fixtures.
The confidence column above separates those evidence levels.

A documented directory tells us where to discover files. It does not define
message boundaries, speaker roles, timestamps, branches, or which fields are
reasoning, tools, and credentials. These mappings need a separate adapter.
An app can change its schema while keeping the same directory.

Users already control source locations: `scan` and `import-auto` accept files
or recursively searched folders anywhere readable, and refresh configuration
can retain those selected paths. Native `sync-local` also has root overrides
for its four existing providers. No source needs to be moved into the project.

The extension approach is a shared discovery/import/reporting pipeline with
small format-specific adapters. Add a recognizable schema, explicit field and
exclusion mapping, synthetic fixtures, and import/retrieval checks for each new
source. Arbitrary JSON, SQLite, Markdown, or an app's name is not enough to
infer a correct conversation history. ZCode MCP-client setup has not been
tested by adding its history importer.

## History imports not supported

The following have **no app-specific importer** in this repository. Their
ability to call MCP, or a vendor-provided export button, does not change this.

| History source | Current status |
| --- | --- |
| Cursor | Not supported |
| GitHub Copilot CLI or VS Code Copilot Chat | Not supported |
| Grok Build | Not supported; Grok Chat JSON is a different supported format |
| DeepSeek Harness | Not supported; DeepSeek Chat JSON is a different supported format |
| Cline | Not supported |
| Roo Code | Not supported |
| Windsurf / Devin Desktop Cascade | Not supported |
| Zed | Not supported |
| Continue | Not supported |
| Microsoft Copilot | Not supported |
| Perplexity | Not supported |
| Mistral Vibe / Le Chat, including Vibe CLI sessions | Not supported |
| Qwen chat website | Not supported; Qwen Code JSON/JSONL is a different supported format |
| NotebookLM chats, sources, and generated reports | Not supported; notebook container metadata only |
| Gemini activity JSON or HTML outside the documented English/CST layout | Not supported |

Other unlisted app-specific formats are not supported. The generic saved-context
format is a manually prepared input contract, not automatic support for another
vendor's export. Future import targets below remain unsupported until an adapter
and representative fixtures are implemented and verified.

## Import content and exclusions

Exclusions depend on the adapter and observed format. They are not a general
redaction pass over message text. Secrets or paths pasted into messages can
remain searchable. See the [privacy guide](privacy/README.md).

| Source | Imported content | Excluded or unavailable content |
| --- | --- | --- |
| ChatGPT | String content parts of all roles and conversation-tree identities; no role-based visible-dialogue filter | Attachment objects and submitted files; text copied into string parts remains |
| Claude | Conversation text; separately supplied projects, project documents, and memories | Conversation attachment fields; project document text is still imported |
| Gemini | Activity prompts and exported responses, grouped into inferred sessions | Uploads and activity-control boilerplate |
| NotebookLM | Notebook container metadata | Source documents and source-file metadata |
| DeepSeek Chat | Request/response text and tree identities | Uploaded-file metadata |
| Grok Chat | Visible human/assistant messages and tree identities | Thinking, system prompts, account/billing data, attachments |
| Codex | Selected user dialogue and final answers | Instructions, environment metadata, reasoning, commentary, tools, identified approval-review sessions |
| Claude Code | Selected dialogue and final answers | Thinking, tools, command records, notifications, attachments |
| Antigravity | Completed visible user/assistant steps | Planning, tools, lifecycle data, incomplete steps |
| OpenCode | Visible user/assistant text | Reasoning, tools, file parts, execution metadata |
| Qwen Code | Visible user/assistant text | Reasoning, tools, execution records, structured file/path/attachment parts |
| ZCode | Non-synthetic visible user prompts and assistant text parts | Reasoning, tools, files, synthetic/ignored text parts, runtime reminders, timeline events, request logs and settings |

Copied material inside otherwise imported text is not removed merely because
it resembles one of these excluded metadata fields. Export formats can change;
support is tied to recognizable structure rather than a brand name alone.

## Importer roadmap

New importers should be added from a vendor-documented export or a
representative sample. We do not guess an undocumented schema and label it as
support.

### Best next targets

Additional structured candidates, still **unsupported**: Gemini CLI documents
native sessions at `~/.gemini/tmp/<project_hash>/chats/` in its
[session guide](https://geminicli.com/docs/cli/session-management/); VS Code
documents a JSON export through **Chat: Export Chat...** in its
[session guide](https://code.visualstudio.com/docs/agents/run/sessions/manage-sessions).
Check their actual schemas and representative fixtures before implementing
adapters. Gemini CLI sessions are distinct from supported Gemini Apps Takeout.

1. **Grok Build:** officially offers `/export` and stores local sessions under
   `~/.grok/`. Add an adapter after checking one exported session or native
   `updates.jsonl` sample.
2. **DeepSeek Harness:** officially documents JSONL and SQLite persistence.
   JSONL storage can be raw or compressed, with versioned generation filenames.
   Inspect the selected export/storage version and a representative sample
   before adding a dependency or decoder.
3. **GitHub Copilot CLI:** officially exports Markdown and HTML. An adapter
   still needs fixtures covering headings and message boundaries. **Cursor:**
   earlier documentation described Markdown export, but that history URL now
   redirects to the docs home; reconfirm the current export route and sample.

### Sample required before implementation

| Source | What is known | Why it is not claimed yet |
| --- | --- | --- |
| Cline | Local task history exists | No stable full-session export schema was found in official docs |
| Roo Code | Local task history exists | Settings export is not conversation export; its contents may include secrets |
| Windsurf / Cascade | Local chat history exists | A general personal conversation export schema was not established by this audit |
| Microsoft Copilot | Microsoft documents activity-history export as CSV | Columns and message relationships need a sample before parsing |
| Perplexity | The referenced guide documents exporting individual answers as PDF, Markdown, or DOCX | Full-account/full-session coverage is not established by that guide; a sample is needed |
| Mistral Vibe / Le Chat | A personal account export route is documented | Its contents and schema need inspection; this is not a claim about Vibe CLI session files |

For these sources, a privacy-safe fixture can be made from a real export by
replacing every title, message, path, account identifier, and timestamp while
preserving only the data structure. The real export remains outside Git.

## Official references

- [Cursor MCP](https://prod.cursor.com/docs/mcp) and [Cursor chat history](https://docs.cursor.com/en/agent/chat/history)
- [Gemini CLI MCP](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/tutorials/mcp-setup.md)
- [GitHub Copilot CLI MCP](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers) and [session export](https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/chronicle)
- [Grok Build MCP](https://docs.x.ai/build/features/mcp-servers) and [commands](https://docs.x.ai/build/modes-and-commands)
- [OpenCode MCP](https://opencode.ai/v2/docs/mcp-servers) and [session export](https://opencode.ai/docs/cli/#export)
- [Cline MCP](https://docs.cline.bot/mcp/mcp-overview)
- [Roo Code MCP](https://docs.roocode.com/features/mcp/using-mcp-in-roo)
- [Windsurf MCP](https://docs.windsurf.com/windsurf/cascade/mcp)
- [Zed MCP](https://zed.dev/docs/ai/mcp)
- [Continue MCP](https://docs.continue.dev/customize/deep-dives/mcp)
- [Qwen Code MCP](https://qwenlm.github.io/qwen-code-docs/en/users/features/mcp/) and [commands](https://qwenlm.github.io/qwen-code-docs/en/users/features/commands/)
- [DeepSeek Harness MCP client](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/mcp/mcp-client/README.md), [session persistence](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/persistence.md), and [JSONL storage](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/session/session-persistence-jsonl/README.md)
- [Perplexity sessions and export](https://www.perplexity.ai/help-center/en/articles/10354769-what-is-a-thread)
- [Microsoft Copilot activity export](https://support.microsoft.com/en-us/privacy/manage-your-copilot-activity-history-in-the-privacy-dashboard)
- [Mistral account export](https://help.mistral.ai/en/articles/347623-how-do-i-export-my-data-from-vibe)
