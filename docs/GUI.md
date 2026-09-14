# Local desktop prototype

The optional `pensieve` command opens a closed wooden door. Click once to open it
into a dark stone chamber: a carved Pensieve on a raised stage, prophecy orbs on
the left, and glass memory bottles on the right. The selectable import bottles
use faceted apothecary glass with engraved metalwork and popping wooden corks. Touch the basin to reveal
**Import a memory** and **Search the waters** in rising silver smoke. Either shelf
opens the separate library; the library is never the entry screen.

The scene uses bundled illustrations with layered animation, not a freely moving
3D world. Smoke drifts above the water and responds to the pointer. **Still the
magic** pauses motion; the system's reduced-motion preference is respected.
**Enter without the transition** skips the opening animation. Buttons support
Tab and Enter/Space. **← Return to chamber** stays at the top-left of the window
in import, search, library and reader views; it returns directly in one click.
Escape closes the current reader or task view when no import
is running. Use **中文 / English** to switch interface language, including menus,
import status, counts and reader controls. Conversation text, titles, provider
names and account labels remain in their original language. Language and motion
preferences last for the current window.

## Install and open

Start in the extracted project folder with the virtual environment from the
[README](../README.md). GUI dependencies are separate from the core installation.
These commands download the optional desktop packages from PyPI and install this
local checkout; there is no shell installer or remote script.

macOS (verified with Python 3.13 / pywebview 6.2.1):

```sh
.venv/bin/python -m pip install '.[gui]'
source .venv/bin/activate
pensieve --database runtime/archive.sqlite
```

Windows PowerShell (GUI unverified):

```powershell
.\.venv\Scripts\python.exe -m pip install '.[gui]'
.\.venv\Scripts\pensieve.exe --database runtime\archive.sqlite
```

Windows needs a working WebView2 runtime. Linux needs a desktop session and a
supported GTK or Qt webview backend; the project does not yet provide a tested
Linux GUI installation recipe. See the upstream [installation guide](https://pywebview.flowrl.com/guide/installation.html).
No standalone signed/notarized app bundle is provided yet.

The default database is `runtime/archive.sqlite` relative to the directory where
you run the command. Prefer an explicit path when launching elsewhere. The
library/import footer shows the exact archive being used. A missing database is created,
and supported schema upgrades run on opening; no import starts automatically.

To work directly from edited sources after installing GUI dependencies:

```sh
PYTHONPATH=src .venv/bin/python -m archive_mcp.gui --database runtime/archive.sqlite
```

A normal `pip install '.[gui]'` copies the code; reinstall after updates to that
checkout, or use the source command above during development.

## Try without private history

Launch with an unused disposable archive, for example:

```sh
pensieve --database runtime/gui-demo.sqlite
```

Open the door, touch the Pensieve, and choose **Import a memory → Choose folder** and select the repository's `fixtures`
folder. Leave auto-detect selected, use an account label such as `synthetic-demo`,
and import. Search for `archive`, then choose a result. The fixture folder
includes deliberately unrecognized evaluation JSON; those files are skipped.

## Import your history

1. Obtain a supported export using the [export guide](EXPORT_GUIDE.md); extract
   ZIPs before selecting them. Use a file or folder picker, or paste a path.
2. Choose a labeled provider bottle, or the unmarked auto-detect bottle. Scroll
   the bottle shelf horizontally to reach local-session formats. **Inspect selection** shows
   recognized files, unrecognized candidates, and files excluded by the format
   filter. Choosing a format does not reinterpret unsupported data as that app.
3. Enter a stable account label. Import different accounts separately. Provider,
   account, and source choices remain in the current window between imports;
   they are not remembered after closing it.
4. Select **Pour into the Pensieve**. Progress advances after each file commits;
   no percentage is invented for parsing the current file. Keep the window open
   until the operation completes; ordinary closing is held while importing.
5. Review new, updated, unchanged, protected, and removed counts. See the
   [count contract](USER_GUIDE.md#read-the-import-counts). Each GUI source file
   has its own operational batch. Returned counts cover successful files only;
   if a later import fails, the result explicitly reports partial completion.

The selected bottle fills with smoke when inspection finds supported files.
After at least one file commits, its wooden cork pops out, the bottle tilts,
and only white memory smoke flows into the basin. The empty bottle withdraws;
the cork does not fall into the water. The result
then reports the actual counts, including any partial failure. A filled bottle
means a source is selected, not that the archive has already changed.

Preview does not import anything. Import scans the selection again, so the
preview is not a frozen snapshot. Normal file/folder imports inspect the chosen
location. The separate one-click action below searches known local-session
locations; neither route performs a whole-computer search.

Gemini activity still replaces that account's activity view: select one complete
HTML file. ZCode requires its app to be closed. NotebookLM imports metadata only.
All source exclusions and revision limits from the CLI apply to the GUI too.

## One-click local-session import

Choose **Find & import local sessions** in the import view. Alternatively, leave
the source path empty with the **Unmarked** bottle selected and press **Pour into
the Pensieve**. Both actions discover and import supported files immediately,
using the account label currently in the form. Nothing is scanned at startup.
Close native apps first, especially apps writing SQLite stores.

Discovery checks these existing adapter locations:

| Source | Location and selected files |
| --- | --- |
| Codex | `$CODEX_HOME/sessions` when set, otherwise `~/.codex/sessions`; recursive JSONL |
| Claude Code | `~/.claude/projects/*/*.jsonl` |
| Qwen Code | `~/.qwen/projects/*/chats/**/*.jsonl` |
| Antigravity | `~/.gemini/antigravity/conversations/*.db` |
| ZCode | `~/.zcode/cli/db/db.sqlite` (observed macOS store) |

Missing folders are skipped. If nothing is found, the UI says so. Repeated imports
use the existing identity/revision rules; unchanged records are not duplicated.
Each file commits separately, and a failure reports the earlier successful files.

This action does not download ChatGPT/Claude/other website exports, search arbitrary
folders, or infer unsupported app formats. OpenCode JSON exports and other custom
locations still use the file/folder picker. For native files belonging to different
accounts, import their folders separately with distinct account labels instead of
combining them under the one-click label. The CLI `sync-local` command retains its
existing four-provider scope; the GUI additionally checks the observed ZCode path.

## Search and read

**Search the waters** changes the view to look down into the basin. Results emerge
as smoke with provider marks, account labels, dates, and excerpts. Click a result
to open its original thread. The shelves open a separate collection browser,
paged in groups of 30; provider/account filters also apply there.

Search uses the existing SQLite FTS keyword/title search. It does not ask an AI
to interpret the question. Provider/account filters narrow the results. Up to
50 ranked candidate matches are grouped into conversations or saved-context
items; a limit notice tells you when to narrow the query. No-hit results do not
prove the whole archive has no related material.

The reader shows original text, dates in your computer's local timezone, and
provider/account/source attribution. Conversation pages contain up to 20 visible
messages. **Load next 20 messages** continues the thread; **Read more** continues
an individual message or saved-context item beyond 4,000 characters. Branch IDs
are available under each message; the list includes retained branches, not just
one selected dialogue path. It is not yet a visual branch tree.

Archived markup, links, and image tags are displayed as plain text. They are not
rendered as HTML, fetched, or executed. After importing, run search again; results
and pagination from the old snapshot are cleared. Also restart a search after
changing the archive through a separate CLI process.

## Local architecture and current limits

The GUI uses [pywebview's native window and Python bridge](https://pywebview.flowrl.com/api/).
Its page, styles/scripts, artwork, and provider marks are bundled in the package.
See [artwork sources and provider marks](ARTWORK.md). It starts no HTTP
listener, makes no model calls, and uses no remote assets or telemetry. Core MCP
installation does not require pywebview, and its tools remain read-only. Dependency
installation still downloads software. [Privacy details](privacy/README.md).

Search/read calls open read-only SQLite connections. Imports use the existing
per-file transaction and adapter logic. One GUI import runs at a time; it is not
a multi-process scheduler. The prototype has no cancellation/resume button,
background capture, automatic refresh, or persistent UI preference store.

Verified on macOS using synthetic sources: door opening, chamber menu, corked provider bottles, source preview, committed
import/pour, overhead search, original messages, and shelf browsing. Chinese UI
switching and one-click local import were exercised with discovery redirected to
synthetic session folders; private native sessions were not imported for UI tests. Native folder
picker, repeat counts, provider/account labels, and branch IDs were also exercised.
Automated tests cover partial failure, exact text pagination, saved context,
source immutability, read-only retrieval, and bridge error privacy. Windows/Linux
native controls and assistive-technology workflows remain unverified. The GUI
has focusable controls, a skip transition, and a motion toggle. The scene is an
illustrated prototype; Windows/Linux rendering, screen-reader behavior, and
performance on older hardware still need dedicated validation.
