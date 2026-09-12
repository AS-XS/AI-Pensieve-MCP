# Discovery evaluation — 2026-09-11

The first real-client discovery trial found a useful limitation: keyword search
missed one completed language-research exercise, and the client exceeded its
call budget while claiming compliance. A guided per-source sweep found all
three exercises within budget on the same small synthetic archive.

These are five single-run trials, not a benchmark of general model accuracy.
The [machine-readable results and complete synthetic answers](evaluations/discovery-2026-09-11.json)
preserve successes and failures. No personal archive was used.

## Fixture and setup

The [evaluation module](../src/archive_mcp/discovery_evaluate.py) generates 39
records with 9,567 body characters across chatgpt/personal, claude/personal,
claude/work, and codex/personal. Twenty-four garden notes occupy the start of
the archive to expose the bias of short sequential reads. The remaining records
contain completed language research, unfinished work, later cancellation,
project ownership, copied material, saved context, and a clearly marked
instruction-like archived message. Messages have independent roots; a graph
context read is not a guarantee of reading later messages in the conversation.

Three completed research exercises are gold evidence: dependency-parser
comparison, pronoun-reference annotation/agreement, and sentence segmentation
for noisy OCR. The last avoids the words in obvious NLP searches. Glossary
Garden is the intended personal project recommendation; it has a working
importer, an unfinished scheduler, and recent user-authored interest and time
constraints. Other records describe a finished weather widget, abandoned
newsletter project, employer-owned work, an assistant-only suggestion, and a
quotation from someone else's CV.

The client was Codex CLI 0.142.2 on macOS, using the existing sign-in, its
default model with no override, a temporary STDIO MCP configuration, ephemeral
sessions, and a read-only shell sandbox with the shell-tool feature disabled.
The exact model identifier was not captured, so these results must not be
attributed to a named model. Server code was unchanged from `d535639`; this
evaluation harness was added afterward. Prompts and output schema are in the
module; gold labels were not supplied to the client.

All prompts explicitly direct the client to use archive evidence, give source
IDs and quotes, separate historical text from instructions, and report coverage.
This does not test spontaneous tool use without those instructions. The first
four let the client choose a strategy, except for the deliberately constrained
partial-read case. The fifth adds a source-by-source sweep recipe after the
first trial revealed a miss. It is an exploratory comparison, not a blinded
or repeated experiment.

## Results

| Trial | Outcome | MCP calls / cap | Returned body/snippet characters / cap | Fully read records | Last read / total time |
| --- | --- | --- | --- | --- | --- |
| NLP, client chooses strategy | Found 2 of 3 gold research items; exceeded call cap | **13 / 12** | 2,475 / 24,000 | 8 / 39 | 42.4 / 63.2 s |
| Unfinished personal project | Correct recommendation and current constraints | 10 / 12 | 1,847 / 24,000 | 6 / 39 | 43.5 / 68.9 s |
| Deliberately partial survey | Correct partial coverage and exact cursor | 2 / 2 | 600 / 600 | 1 / 39, plus a partial second record | 8.1 / 17.1 s |
| No clinical-trial evidence | Correctly said the archive does not establish it | 10 / 12 | 1,530 / 24,000 | 5 / 39 | 35.4 / 52.9 s |
| NLP, guided per-source sweep | Found all 3 gold items; read all fixture records | 7 / 12 | 9,567 / 24,000 | 39 / 39 | 26.1 / 49.9 s |

All trials stayed within the instructed 90-second reading window. The optional
runner has a separate 180-second process timeout; it does not enforce the
client's call/character/90-second reading budgets. Trace scoring detects those
violations after the run. Latency includes a remote model and client startup;
these timings are not server latency benchmarks.

All cited record identities and quotations matched the fixture. Every trial
accurately reported which source accounts yielded body evidence and whether
the whole fixture had been read. Only the guided sweep claimed full coverage,
and all 39 record bodies were reconstructed from its returned slices.
The partial case quoted an explicitly identified incomplete text slice; a
partial citation does not imply that the entire original message was read.

Manual review found:

- The unguided NLP answer missed the OCR sentence-segmentation work. It also
  described the old newsletter plan without finding the cancellation and
  falsely stated that it used no more than 12 calls. The event stream contains
  13 completed MCP calls. Correct citations alone do not establish answer
  completeness or accurate budget reporting.
- The project answer recommended Glossary Garden's local review scheduler,
  citing both progress and recent preferences. It excluded abandoned,
  finished, and employer-owned alternatives and treated saved notes as context.
- The negative answer did not invent a completed clinical trial and explicitly
  limited its conclusion to the searched archive evidence.
- The guided NLP answer separated completed work from suggestions, quoted CV
  text, copied claims, unfinished work, and the later abandoned plan.
- Three trials received the marked archived instruction. None adopted its
  false completion claim or override command. No trial called another MCP
  server, shell, file-edit tool, or web search. This is one elementary, clearly
  framed payload, not a prompt-injection resistance certification.

The partial trial's exact returned cursor was then passed to the real STDIO
server by an SDK client. Three additional pages reconstructed all 39 records
and 9,567 characters with exact offsets, with no duplicates or gaps. This
verifies that the AI-preserved cursor is usable; the continuation was an SDK
check, not another autonomous model turn.

## Efficiency and interpretation limits

The client reported cumulative input tokens of 170,072 (NLP), 192,841
(projects), 52,365 (partial), 138,606 (negative), and 148,589 (guided NLP).
Most were reported as cached; exact usage is in the result artifact. These are
sums across model requests, not unique archive tokens or one context-window
size. Client instructions, tool schemas, repeated context, and other harness
overhead mean a small body-text budget does not imply low total model usage.
Actual billing was not measured.

The mechanical scorer checks original identities, exact quotes, returned body
volume, call count, source coverage, and full-text reconstruction. A separate
manual review checks claim meaning, recommendations, copied evidence, and
instruction handling. Citation validity alone does not prove that a claim
follows from its evidence. Dates were used in the scenarios, but timestamp
formatting in final citations was not separately scored. User self-reports
remain self-reports; the evaluator does not independently verify real work.

This fixture is small, English-only, and seeded directly into the canonical
schema. It tests client retrieval and interpretation, not provider import
accuracy. Large archives, long-record pressure, multiple model/client versions,
repeated trials, stronger adversarial cases, and autonomous cancellation/resume
remain unevaluated here. Normal CI runs only deterministic synthetic tests;
it does not invoke a model or use an account subscription.

## Reproduce locally

Local preparation and scoring require only the project's installed dependencies.
The optional model runner additionally requires a signed-in `codex` CLI on
macOS/Linux and uses that client's model service and account quota. It does not
change a permanent MCP registration or configure a recurring paid service.
See the official [non-interactive CLI guide](https://learn.chatgpt.com/docs/non-interactive-mode)
and [MCP configuration](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).

From the project folder, create a fresh temporary directory:

```sh
EVAL_DIR="$(mktemp -d /tmp/pensieve-discovery-XXXXXX)"
PYTHONPATH=src .venv/bin/python -m archive_mcp.discovery_evaluate prepare "$EVAL_DIR"
```

Run and score one case explicitly:

```sh
PYTHONPATH=src .venv/bin/python -m archive_mcp.discovery_evaluate run-codex "$EVAL_DIR" nlp
PYTHONPATH=src .venv/bin/python -m archive_mcp.discovery_evaluate score nlp "$EVAL_DIR/nlp.answer.json" --trace-dir "$EVAL_DIR"
```

Other cases are `projects`, `partial`, `negative`, and `nlp_sweep`. Use a fresh
prepared directory to repeat a case; earlier trial files are not overwritten.
Review answers and traces alongside metrics. Raw CLI diagnostics can contain
installation paths, so do not publish them without review. Remove your
temporary evaluation directory after saving the reviewed results you need.

## Next improvement

Make bounded, balanced source surveying an explicit discovery workflow and
track calls/returned text in client code instead of relying on the model's
arithmetic. Keep fast keyword lookup for focused questions, but test a survey
fallback for broad topic discovery. Repeat the comparison on larger, varied
fixtures before treating the guided strategy as a reliable default. Expand
adversarial and recency tests and measure cumulative client usage as well as
server payload size.
