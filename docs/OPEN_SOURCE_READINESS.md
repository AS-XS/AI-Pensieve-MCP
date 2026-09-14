# Release readiness

The local retrieval prototype exists. A public repository and a trustworthy
product release have different completion criteria. This is an outstanding
checklist, not a security certification.

## Before a public release

- [x] Add the [Apache License 2.0](../LICENSE) and [copyright notice](../NOTICE), selected by the owner on 2026-09-11.
- [x] Complete the bounded [implementation review](privacy/REVIEW.md) and fix the reproduced error/log leaks.
- [x] Document trusted local access to the selected database; no permission layer or routine hashing is required.
- [x] Document [export routes and format limits](EXPORT_GUIDE.md), and implement explicit native provider selection.
- [x] Verify deletion/rebuild behavior and schema upgrades; document unsupported export variants and source-version limits.
- [x] Provide a temporary synthetic demo that verifies import, integrity, real STDIO pagination/comparison, and original-message retrieval locally on macOS and in Ubuntu/Windows CI.
- [x] Verify the Git-eligible source layout in isolation from local configuration and private archives; 79 tests, demo, and evaluation pass using installed dependencies. See [verification scope](DEVELOPMENT.md).
- [x] Add CI and contributor/security reporting guidance.
- [x] Enable GitHub private vulnerability reporting for the public repository and verify the enabled state (2026-09-14). See [security reporting](../SECURITY.md).
- [x] Review all root Markdown and public documentation against implementation and official sources; record corrections and verification limits in [documentation audit](DOCUMENTATION_AUDIT.md).
- [x] Confirm successful Ubuntu/Windows CI runs on Python 3.10 and 3.13 for `f68bb1d`; see the [run and scope](CLIENT_VERIFICATION.md#github-ci).
- [x] Review intended source files and local Git history for private material before the initial upload; publish a clean initial history with a GitHub noreply author address. This bounded review is not a secret-detection guarantee.
- [x] Test a clean clone of the initial source commit on macOS/Python 3.13: 79 tests and the real STDIO demo passed; retrieval evaluation reproduced its documented lexical-search limitation.
- [x] Validate a fresh dependency installation from requirements.txt in that clone, including pip check.
- [x] Connect Codex CLI to a synthetic archive using the published source and a temporary configuration; see [client verification](CLIENT_VERIFICATION.md#codex-cli).
- [x] Record the CLI version, OS, configuration method, and successful status/search/evidence/comparison calls. Only this tested scope is promoted; other app integrations and permanent-registration setup remain unverified.
- [x] Add [example prompts](EXAMPLE_PROMPTS.md), validate their arguments over STDIO, and document provenance and coverage limits; the original 12-tool check is now extended with the balanced survey tool.
- [x] Handle empty native sessions, reject missing selected import paths, and consistently accept UTF-8 byte-order marks; verify with synthetic regression tests.
- [x] Select [AI Pensieve MCP](https://github.com/AS-XS/AI-Pensieve-MCP), link the README download route, and configure the local Git origin.
- [x] Upload the reviewed initial source to the selected repository and verify its main branch on GitHub (2026-09-10).
- [ ] Complete remaining release checks and publish a versioned release. The repository is public as of 2026-09-14; public visibility alone is not a versioned release.

A GUI, semantic search, and personal reflection are later milestones. They are
not necessary to release a useful developer archive.

Current privacy limits are explained in the [privacy guide](privacy/README.md).
Test commands are in [development](DEVELOPMENT.md).
Historical completed work is kept in the local project notes.
