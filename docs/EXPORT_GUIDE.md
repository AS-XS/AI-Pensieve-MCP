# Export history from your apps

Official references rechecked **2026-09-09**. Export menus and file formats can
change. The steps below identify official download routes; supported contents
describe this repository's observed formats, not everything a vendor exports.
DeepSeek's exact menu sequence and NotebookLM's product-specific export layout
could not be confirmed from current official help and are marked below.
See [unsupported history sources](COMPATIBILITY.md#history-imports-not-supported)
for apps and formats with no importer. A listed MCP client is not automatically
a supported history source.

## Import the files you choose

1. Download from the provider while signed into the account you want to archive.
2. Extract ZIP/TGZ downloads locally and keep the original download unchanged.
3. Put selected files in a folder such as imports/account-one/chatgpt. Keep
   accounts separate; importing a folder reads supported files recursively.
4. Run import-auto with that file or folder and a stable account label.

macOS/Linux, from the installed project folder:

~~~sh
PYTHONPATH=src .venv/bin/python -m archive_mcp import-auto runtime/archive.sqlite imports/account-one/chatgpt --account account-one
PYTHONPATH=src .venv/bin/python -m archive_mcp import-report runtime/archive.sqlite
~~~

Windows PowerShell:

~~~powershell
$env:PYTHONPATH = (Resolve-Path src).Path
.\.venv\Scripts\python.exe -m archive_mcp import-auto runtime\archive.sqlite imports\account-one\chatgpt --account account-one
.\.venv\Scripts\python.exe -m archive_mcp import-report runtime\archive.sqlite
~~~

Replace the input path with the selection described for your app below. Names
of staging folders are your choice. To preview format counts without importing,
use `scan INPUT_PATH` in place of `import-auto ...`; this is optional and reads
the selected files to recognize their formats. It is not a hash check.

## ChatGPT

In ChatGPT, open your profile menu, then Settings → Data controls → Export
data → Export, and confirm. Download and extract the ZIP when it is ready.
OpenAI also offers a Privacy Portal route. Workspace eligibility varies;
Business, Enterprise, and Healthcare workspaces do not offer self-service
export. See [OpenAI's export instructions](https://help.openai.com/en/articles/7260999-how-do-i-export-my-data).

**Select:** the conversation JSON, commonly conversations.json, from the
extracted export. Put it in imports/account-one/chatgpt and use the command above.
The adapter reads the observed conversation-tree JSON format, including branches
and string content parts of every role. Those parts can include system or tool
text; it does not enforce a visible-dialogue filter for ChatGPT. It does not
import chat.html or attachment objects/files.

## Claude

On the web app or Claude Desktop, open your account menu, then Settings →
Privacy → Export data. Download through the emailed link. Mobile apps do not
start this export; organization exports require the Primary Owner. See
[Anthropic's export instructions](https://support.claude.com/en/articles/9450526-export-your-claude-data).

**Select:** conversation JSON, commonly conversations.json, into
imports/account-one/claude. Import that folder with the same command pattern.
If wanted, also select supported project JSON and memory JSON from the export;
project documents are included when their containing project JSON is imported.
Import only the conversation file if you want conversation history alone.

The adapter recognizes conversations containing chat_messages, individual
project objects with docs/prompt_template, and the observed conversation/project
memory format. Other Claude JSON layouts are not automatically supported.
Conversation attachment fields are excluded; selected project document text is
imported.

## Gemini Apps

In Google Takeout, choose Deselect all, then My Activity → All activity data
included → Deselect all → Gemini Apps. Choose an email download, Export once,
and ZIP, then create and download the export. The separate Gemini product
selection is for Gems; chat activity uses My Activity. See
[Google's Gemini export instructions](https://support.google.com/gemini/answer/16920332?hl=en).

**Select:** the Gemini Apps activity HTML, commonly MyActivity.html. If Takeout
offers an activity-format choice, choose HTML. Put only the Gemini activity
file in imports/account-one/gemini; do not pass a mixed Google activity export.
The archive imports prompts and available responses, excluding uploads, and
groups activity into inferred sessions rather than original conversation IDs.

**Current format limit:** the parser supports the observed English HTML with
CST timestamps interpreted as UTC−06:00. Other languages/timezones and JSON
activity exports are not supported. A recognized filename alone does not mean
the entries were parsed: check the import report for no_indexable_records.
Do not rename a JSON export to HTML to bypass this limit.

## NotebookLM

Use [Google Takeout](https://takeout.google.com/) and select NotebookLM if it is
offered for your account, then download and extract the archive. Google's
[general download guide](https://support.google.com/accounts/answer/3024190?hl=en)
explains the product selection and download process. A current official
NotebookLM-specific file-layout guide was not located during this check.

**Select:** notebook metadata JSON into imports/account-one/notebooklm. The
observed supported object contains a title and metadata.createTime. Importing
it makes notebook metadata searchable, not notebook chats, source documents,
or generated reports. A notebook exported as a Google Doc or PDF is not a
supported input for this adapter.

## DeepSeek Chat

Open the chat app's settings and look for its history copy/data export option.
DeepSeek's [official privacy policy](https://cdn.deepseek.com/policies/en-US/deepseek-privacy-policy.html)
documents copying history through settings and a contact route for data
requests. It does not specify the current button sequence, download timing,
or file schema; those details remain unverified here.

**Select:** the extracted chat conversation JSON into
imports/account-one/deepseek. The supported export is a list of conversation
trees whose messages contain REQUEST/RESPONSE fragments. Visible dialogue and
tree relationships are imported; uploaded-file metadata is excluded. API
billing/usage exports and DeepSeek Harness sessions are different formats.

## Grok Chat

Use Grok.com or the Grok mobile app: Settings → Data Controls to download
account data, then extract the download. See the
[official consumer FAQ](https://x.ai/legal/faq).

**Select:** the JSON containing chat conversations into imports/account-one/grok.
The observed export has a top-level conversations list, with conversation and
responses entries. The adapter imports visible dialogue and tree identities;
thinking, attachment fields, and account/billing files are excluded. This
supports the observed Grok chat export, not every X archive or Grok Build export.

## OpenCode

Run `opencode export SESSION_ID` to export a session as JSON; omit SESSION_ID
to select a session interactively. Save the JSON output into a file such as
imports/account-one/opencode/session.json, then import that file. See the
[official CLI reference](https://opencode.ai/docs/cli/#export).

For example, after creating the destination folder, save UTF-8 JSON:

macOS/Linux:

~~~sh
opencode export SESSION_ID > imports/account-one/opencode/session.json
~~~

Windows PowerShell:

~~~powershell
opencode export SESSION_ID | Set-Content -Encoding utf8 imports/account-one/opencode/session.json
~~~

The adapter reads the observed info/messages JSON structure and imports visible
user/assistant text. Reasoning, tool records, file parts, and execution metadata
are excluded. Do not use a public share link as an archive input.

## Qwen Code

In the session, run `/export json` or `/export jsonl`. Copy the resulting file
into imports/account-one/qwen-code and import that folder. The official
[command guide](https://qwenlm.github.io/qwen-code-docs/en/users/features/commands/)
also lists HTML and Markdown exports, which this archive does not import.

Supported JSON/JSONL retains visible user/assistant text. Reasoning, tools,
execution records, and structured file/attachment parts are excluded.

## Existing local coding sessions

Codex, Claude Code, Antigravity, and Qwen Code can be imported from supported
local session stores without requesting an account export. Choose providers
and locations using the [native-session guide](USER_GUIDE.md#native-coding-sessions).
Those paths describe the stores recognized by this implementation; app versions
and installations can differ. Selecting a native app imports only files that
match its documented local discovery pattern.

Finish session writes before importing; close Antigravity before reading its
native database (see the native-session guide). For a few sessions, pass their
JSONL files or a supported Antigravity .db file
directly to import-auto. Local adapters keep selected visible dialogue and
exclude tool/reasoning records as detailed in
[content and exclusions](COMPATIBILITY.md#import-content-and-exclusions).

## When an export does not match

Read the import report: unrecognized_format means the structure was not
recognized; no_indexable_records means the adapter reported no message nodes
or saved-context records. This warning does not measure nonempty text or titles.
The [user guide](USER_GUIDE.md#check-imports) explains other warning codes and
the optional integrity check. An empty export can be unrecognized by automatic
detection because it contains no records from which to infer its provider.

This archive accepts structured history, not arbitrary PDFs, Word files,
screenshots, shared-chat URLs, or prose copied from an AI. Keep an unsupported
export unchanged for a future adapter. Metadata exclusions do not scrub secrets
inside message text; see [privacy and data flow](privacy/README.md).

Text inputs should be UTF-8. BOM handling is currently adapter-specific:
OpenCode and Qwen's readers accept a UTF-8 BOM, but several other JSON readers
do not, even when automatic JSON detection recognizes the file. A recognized
format therefore does not guarantee a successful import. Preserve the original
and use a UTF-8 copy without a BOM if an affected adapter rejects it.
