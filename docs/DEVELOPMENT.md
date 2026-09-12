# Development checks

Use synthetic fixtures for automated tests. Keep exports, databases, logs,
source maps, and private evaluations out of Git.

macOS/Linux, after README setup:

~~~sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=src .venv/bin/python -m archive_mcp.evaluate
PYTHONPATH=src .venv/bin/python -m archive_mcp.demo
~~~

Windows PowerShell:

~~~powershell
$env:PYTHONPATH = (Resolve-Path src).Path
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m archive_mcp.evaluate
.\.venv\Scripts\python.exe -m archive_mcp.demo
~~~

With Make, use make test, make demo, and make evaluate. The temporary demo is
also described in [demo](DEMO.md). The demo now verifies a real STDIO server
connection, paginated enumeration, comparison, and original-message retrieval.
CI is configured to run the suite and demo on Ubuntu and Windows with Python
3.10 and 3.13; all four jobs passed for `f68bb1d` in the
[verified CI run](CLIENT_VERIFICATION.md#github-ci). The checks do
not read user exports or runtime databases.
Check an imported database using the [user guide](USER_GUIDE.md#check-imports).

On 2026-09-09, all 79 tests, the demo, and the retrieval evaluator passed on
macOS/Python 3.13 from an isolated copy of Git-eligible source files, using a
directory name containing spaces. The copy excluded local configuration,
private archives, environments, and project notes. Existing installed
dependencies were reused: this was source-layout verification, not a fresh
dependency install or a clean clone of the final release commit. The demo
enumerated eight conversations across three pages, searched eight sources, and
resolved original-message evidence from seven sources. Local Markdown file
links also resolved within the source copy.

On 2026-09-10, a clean Git clone of the initial source commit was tested on
macOS/Python 3.13 in a directory containing spaces. A new virtual environment
installed requirements.txt without using the package cache; pip check found
no dependency conflicts. All 79 tests and the real STDIO demo passed. The
retrieval evaluation found 9 of 10 positive cases and returned no results for
the negative case, reproducing the documented synonym-search limitation.
That installation check did not validate an external AI application or remote
CI. Subsequent [client and CI verification](CLIENT_VERIFICATION.md) records
the separate results and their scope.

See [retrieval evaluation](RETRIEVAL_EVALUATION.md) for scoring and limitations,
and [archive sweep](ARCHIVE_SWEEP.md) for keyword-free traversal.

On 2026-09-11, all 87 tests passed from an isolated Git-eligible source copy
under `/tmp`, reusing installed dependencies on macOS/Python 3.13. All 12 JSON
tool examples passed over STDIO; the updated demo discovered 12 tools and swept
26 nonempty-message/saved-context records in two pages. The lexical evaluator
remained at 9/10 positive cases and one correct negative case. These new changes
have not yet been checked by the remote CI run cited above.

An initial warm local database-helper benchmark swept 10,000 messages plus
1,000 saved records, each with 1,000 body characters. It reconstructed all 11
million characters by aggregate record/character counts in 688 pages at a
16,000-character/50-slice page budget. Exact slice reconstruction and duplicate
identity detection are covered separately by the regression tests.
Traversal took approximately 0.094 seconds; the slowest page took 0.39 ms on
that run. This excludes fixture generation, MCP transport/serialization, model
latency, and token costs. It is not a production latency or memory guarantee;
large individual records and other archive layouts still need benchmarking.

See also
[real-client discovery evaluation](DISCOVERY_EVALUATION.md) for the five
synthetic trials, the observed recall/call-budget failure, and the guided sweep
comparison. Its optional model runner is separate from ordinary tests and CI.
All 98 deterministic tests passed locally after adding the evaluation harness.

To repeat discovery checks on larger synthetic archives, prepare a fresh
temporary directory with `--seed 11 --size 1000`. A seed changes evidence
positions and unrelated filler; completed-work and project-status evidence stay
fixed. The generated `corpus.json` is the scoring reference for that directory.
For example, after choosing a fresh `EVAL_DIR`:

~~~sh
PYTHONPATH=src .venv/bin/python -m archive_mcp.discovery_evaluate prepare "$EVAL_DIR" --seed 11 --size 1000
PYTHONPATH=src .venv/bin/python -m archive_mcp.discovery_evaluate run-codex "$EVAL_DIR" nlp --enforce-budget
PYTHONPATH=src .venv/bin/python -m archive_mcp.discovery_evaluate score nlp "$EVAL_DIR/nlp.answer.json" --trace-dir "$EVAL_DIR"
~~~

Repeat `projects` in the same directory, or use fresh directories for other
seeds/repetitions. Model runs use the existing client's service and quota;
ordinary tests remain local. `--enforce-budget` enables the dedicated server's
read limits. Scoring distinguishes client attempts, successful server reads,
budget rejections, returned body volume, and cumulative client tokens. Review
the answers as well: valid quotations do not establish correct interpretation.
Remove the temporary directories after retaining the findings you need.

See also
[MCP tools](MCP_TOOLS.md) for interface behavior, and
[release readiness](OPEN_SOURCE_READINESS.md) for publication checks.
The [documentation audit](DOCUMENTATION_AUDIT.md) records the subsequent full
documentation review and fresh synthetic verification on 2026-09-09.
