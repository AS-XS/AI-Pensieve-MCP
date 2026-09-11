# Documentation audit — 2026-09-09

Later client/platform results are recorded in [client verification](CLIENT_VERIFICATION.md).
The dated audit sections below retain their original verification scope.

The 2026-09-11 implementation follow-up fixes the empty-native-session,
missing-selected-path, and UTF-8 BOM issues recorded below, and adds
[bounded saved-context/message traversal](ARCHIVE_SWEEP.md). Historical
observations below describe the earlier revision, not current failures.

The later 2026-09-11 ZCode follow-up adds an observed-format SQLite importer,
custom-folder instructions, and explicit separation of official export contracts
from local schema observations. Six new synthetic tests pass (93 total), and a
local source was reconciled against imported IDs and retrieved through MCP.
The owner also changed the current license from MIT to Apache-2.0; earlier
license/publication statements below describe their original audit date.

Reviewed the full text of all 20 existing root Markdown files and public guides,
including local planning instructions and the dated development log. Checked
current implementation claims against source, schemas, fixtures, and tests;
checked external setup/export claims against official references. Corrections
are in the affected guides, rather than only listed here.

This is a documentation review of the working tree. It is not a certification
of every provider export, third-party client, operating system, or historical
measurement. Ignored private runtime reports, provider exports, dependencies,
and Git history were outside this documentation scope.

## File coverage

| Document | Evidence and review focus |
| --- | --- |
| [README](../README.md) | Dependency requirement, CLI install/import/use, local/client disclosure, canonical-record idempotence |
| AI client setup | Official transport/configuration references; version and platform verification limits |
| Compatibility | Adapter code and synthetic fixtures; client/import distinction; external export claims |
| Export guide | Official download routes; exact observed parser structures and exclusions |
| User guide | CLI parser, discovery, refresh, batch reporting, native selection, failure behavior |
| MCP tools | All 11 registered tool signatures, retrieval SQL, limits, date formats, logging and migration behavior |
| Schema | SQL definitions, migration code, every adapter's field mappings and identity limits |
| Data lifecycle | Per-file transactions, upsert/replacement behavior, rebuild tests, official SQLite backup documentation |
| Retrieval evaluation | Evaluator and labels, current synthetic output, separation from private historical results |
| Synthetic demo | Subprocess/temporary-directory implementation, timeout and error boundaries, fresh successful run |
| Development | Actual test/demo/evaluator commands and CI matrix; historical isolated-copy scope |
| Release readiness | Existing files, configured CI, absent license/remote, remaining release decisions |
| Privacy README | Import/retrieval code, client disclosure, content exclusions, logs and deletion limits |
| Privacy review | Dated findings and regressions; clarified historical test count and later demo subprocess |
| CONTRIBUTING | Current checks and change expectations; private reporting channel remains to be configured |
| SECURITY | Actual local trust model and disclosure guidance; no invented contact address |
| AGENTS.md (local) | Source immutability and user constraints; corrected batch-transaction and warning expectations |
| PLAN.md (local) | Implemented versus proposed capabilities, identity mappings, optional GUI and reflection |
| TODO.md (local) | Completion evidence and remaining work, including concrete importer limits and saved-context sweep gaps |
| DEVLOG.md (local) | Every dated entry reviewed for historical/current distinction; original measurements retained as dated claims |

## Corrections that affect use

- The README imports one explicitly labeled account folder, so following its
  commands does not combine every account under the default label.
- Cline's current CLI path is `~/.cline/mcp.json`; removed the unsupported
  CLI/IDE shared-file claim. Cursor's current STDIO field table requires `type`.
  Updated Zed's menu sequence and Qwen's MCP manager instruction.
- OpenAI now describes the shared desktop configuration under ChatGPT desktop;
  clarified that this does not make local configuration available to ChatGPT web.
  Windsurf's reference redirects to Devin Desktop while retaining the old path.
  Antigravity's unversioned plugin check is explicitly a historical workaround.
- Perplexity's referenced export is an individual answer, not a demonstrated
  full-session/account archive. Microsoft documents CSV export. Cursor's old
  history reference now redirects away from the export instructions. Added more
  precise Microsoft, Mistral, and DeepSeek persistence references.
- ChatGPT imports string parts across roles, potentially including system/tool
  text. Exclusion claims now describe fields rather than promising only visible
  dialogue. Documented Codex's review-prefix heuristic and reconstructed parents.
- Fixed the schema's nullable-field description, required-date limitations,
  transaction granularity, and the distinction between importing sources and
  opening a database backup.
- Documented node-based empty warnings, silent zero-candidate discovery for
  missing paths, empty native-session failures, and the need to stop Antigravity
  writes before its immutable SQLite read.
- Clarified plural search filters versus singular lookups, empty filter lists,
  numeric versus ISO dates, empty-node counts, graph/page ordering, and the
  absence of exhaustive saved-context enumeration/continuation. FTS snippets
  have token windows, not a fixed character/byte budget.
- Documented that `import-report` can initialize/migrate a database and `check`
  needs a writable connection for rolled-back FTS commands. An `ok: false`
  integrity result does not itself make the CLI exit nonzero.
- Narrowed log/error guarantees to the archive's own handlers; documented demo
  startup/forced-termination limits. Kept historical counts and backup decisions
  separate from current policy. Identified the missing security contact route.

## Validation and limits

All 79 synthetic tests passed on macOS/Python 3.13 during this audit. The real
STDIO demo passed with 11 read-only tools, eight conversations over three pages,
eight examined sources, and original-message evidence from seven sources.
The evaluator reproduced 9/10 positive cases and 1/1 correct empty result, with
MRR and mean recall 0.90; the deliberate synonym miss remains.

Mechanical checks covered all 21 Markdown files including this report: 76 local
file/anchor links, nine JSON/JSONC examples, one TOML example, 28 shell blocks,
24 archive CLI examples parsed against the actual command parser, and exact
agreement between the documented and registered 11-tool inventory. These
syntax checks do not execute vendor registration commands or PowerShell.

Additional temporary synthetic checks reproduced zero candidates for a missing
path, an empty node without an empty-record warning, an empty Claude Code
session failure, and `check` returning `ok: false` with exit code 0. They also
confirmed OpenCode accepts a UTF-8 BOM while ChatGPT's reader rejects it.

Official references are linked in the client, compatibility, export, and
lifecycle guides. Reference availability and documented contracts do not prove
successful setup in each app. No fresh provider export, Windows execution,
Ubuntu/Windows CI run, dependency installation, or release-clone test was done
in this audit. DeepSeek's exact export UI and NotebookLM's current vendor schema
remain unverified. Historical private archive counts were not remeasured.

The review changed documentation only. No private database was opened, imported,
refreshed, deleted, or backed up. Runtime behavior was not changed to make the
documentation claims appear true; concrete implementation gaps are recorded in
the local TODO and relevant public guides.

## Follow-up: all-client support labeling — 2026-09-10

Rechecked the non-OpenAI references for Claude Code, Claude Desktop,
Antigravity, Cursor, Gemini CLI, GitHub Copilot CLI, Grok Build, OpenCode v2,
Cline, Roo Code, Windsurf/Cascade, Zed, Qwen Code, DeepSeek Harness, and Continue.
The [compatibility matrix](COMPATIBILITY.md#mcp-clients) now attaches an official
contract and archive-integration evidence to each entry. Every setup section
also carries its status, including OpenAI entries.

The earlier shared disclaimer was insufficient: a vendor's documented STDIO
transport is not proof that this archive was tested in its app. No current
third-party integration was executed during this documentation review. Earlier
Codex registration and Antigravity calls remain historical evidence with their
limits. The bundled SDK demo is identified separately.

Removed the unverified Antigravity workspace plugin recipe and the unsupported
assertion that Grok Build's Windows TOML setup works. Windows path substitutions
are explicitly syntax examples conditional on client support, not platform tests.
Added explicit unsupported direct connections and absent history importers;
split Claude Desktop from Claude Code, web/mobile apps from coding harnesses,
and Continue Agent mode from modes without documented MCP tool use.

The detailed guides remain available for officially documented configurations,
marked untested rather than blindly promoted to supported or falsely declared
technically impossible. Unknown clients remain unverified. Missing importers
and server transports are labeled not supported.

Follow-up validation passed across 21 Markdown files: 85 local links/anchors,
nine JSON/JSONC blocks, one TOML block, 28 shell blocks, and 24 archive CLI
examples. All 15 client/reference setup sections have an explicit status.
Whitespace checks passed. These were documentation checks, not new app tests.
