# Release readiness

The local retrieval prototype exists. A public repository and a trustworthy
product release have different completion criteria. This is an outstanding
checklist, not a security certification.

## Before a public release

- [x] Add the [MIT license](../LICENSE) for straightforward reuse and contribution.
- [x] Complete the bounded [implementation review](privacy/REVIEW.md) and fix the reproduced error/log leaks.
- [x] Document trusted local access to the selected database; no permission layer or routine hashing is required.
- [x] Document [export routes and format limits](EXPORT_GUIDE.md), and implement explicit native provider selection.
- [x] Verify deletion/rebuild behavior and schema upgrades; document unsupported export variants and source-version limits.
- [x] Provide a temporary synthetic demo that verifies import, integrity, real STDIO pagination/comparison, and original-message retrieval on macOS; Windows commands are documented but not executed here.
- [x] Verify the Git-eligible source layout in isolation from local configuration and private archives; 79 tests, demo, and evaluation pass using installed dependencies. See [verification scope](DEVELOPMENT.md).
- [x] Add CI and contributor/security reporting guidance.
- [ ] Configure a concrete private security reporting channel before publishing.
- [x] Review all root Markdown and public documentation against implementation and official sources; record corrections and verification limits in [documentation audit](DOCUMENTATION_AUDIT.md).
- [ ] Confirm successful Ubuntu/Windows CI runs on Python 3.10 and 3.13; configuration alone is not platform validation.
- [x] Review intended source files and local Git history for private material before the initial upload; publish a clean initial history with a GitHub noreply author address. This bounded review is not a secret-detection guarantee.
- [ ] Commit the intended release and test a clean clone.
- [ ] Validate a fresh dependency installation and set up a chosen AI client from that release.
- [ ] Record app name, version, OS, registration, and successful archive tool calls before promoting a documented configuration to tested integration support. The SDK demo does not validate third-party apps.
- [x] Select [AI Pensieve MCP](https://github.com/AS-XS/AI-Pensieve-MCP), link the README download route, and configure the local Git origin.
- [ ] Publish the reviewed release to the selected repository; remote configuration does not publish local changes.

A GUI, semantic search, and personal reflection are later milestones. They are
not necessary to release a useful developer archive.

Current privacy limits are explained in the [privacy guide](privacy/README.md).
Test commands are in [development](DEVELOPMENT.md).
Historical completed work is kept in the local project notes.
