# Client and platform verification

Checked on 2026-09-10. These results apply to the versions, source revision,
and flows below; they are not blanket compatibility claims.

The subsequent 2026-09-11 import/sweep changes passed 87 local tests and
12 documented STDIO calls, as recorded in [development](DEVELOPMENT.md).
The historical CI and Codex results below do not cover that newer tool yet.

## GitHub CI

[Run 34554072217](https://github.com/AS-XS/AI-Pensieve-MCP/actions/runs/34554072217)
completed successfully for source commit
`f68bb1dce890c2a768827a2ea523aebc3bb872ca`.
All four jobs passed:

| GitHub runner | Python | Result |
| --- | --- | --- |
| Ubuntu latest | 3.10 | Passed |
| Ubuntu latest | 3.13 | Passed |
| Windows latest | 3.10 | Passed |
| Windows latest | 3.13 | Passed |

The workflow installs requirements, runs the synthetic unittest suite, runs
the real STDIO demo, and checks its success fields. This validates those
automated server flows on the runners. It does not verify an AI application's
Windows/Linux registration, vendor export UI, or every native session format.
The runner labels are moving labels, not a promise about a fixed OS version.
The repository is currently private; viewing these CI links requires access.

## Codex CLI

| Item | Verified scope |
| --- | --- |
| Client | `codex-cli 0.142.2` |
| Host | macOS 26.6.2, arm64 |
| Server runtime | Python 3.13.7, MCP SDK 2.1.1 |
| Source | Clean local clone of the published `f68bb1d` revision |
| Data | Synthetic ChatGPT, Claude, and saved-context fixtures only |
| Connection | Local STDIO under the temporary name `pensieve_smoke` |
| Configuration | Command-line MCP override; `--ignore-user-config`, `--ephemeral`, and read-only shell sandbox |

The test used the already-installed server dependencies and the CLI's existing
sign-in. Source, synthetic database, audit log, and captured client output were
isolated under `/tmp`. It did not replace a user's registered archive. No
permanent MCP registration was added. The separate fresh-install check is
recorded in [development](DEVELOPMENT.md).

The client received an explicit request to check status, search for `archive`,
retrieve an original message, and cross-reference sources. Its JSON event
stream confirmed successful calls to:

1. `archive_status`
2. `search_conversations`
3. `get_message`
4. `cross_reference`

The final response identified the ChatGPT and Claude conversations, reported
the saved-context source's no-match result, and quoted the original synthetic
user question with provider, account, conversation ID, and message ID. The
event stream contained no shell-command execution. Temporary test artifacts
were removed after validation.

This verifies explicit retrieval through that CLI version. It does not test
the desktop settings UI, IDE extension, permanent `codex mcp add` registration,
other models, all 11 tools through Codex, or spontaneous history search for an
unprompted task. Other client statuses remain in [compatibility](COMPATIBILITY.md).

The relevant client options and STDIO configuration are documented in the
[official CLI reference](https://learn.chatgpt.com/docs/developer-commands?surface=cli)
and [MCP guide](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).

## Example-prompt checks

On 2026-09-10, the then-current 11 JSON calls in the [example-prompt guide](EXAMPLE_PROMPTS.md) were parsed
from the document and executed through a real STDIO server against the stated
synthetic fixtures. Message and conversation-list continuation were checked,
and the suggested NLP/project query syntax was accepted. This verifies tool
arguments and the cited synthetic evidence, not the quality of every natural-
language answer a model might produce.
