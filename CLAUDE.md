# Snitch — project rules for Claude Code

## What we are building
Snitch is the integrity layer for AI coding agents. It detects when an agent makes
tests pass by cheating (editing/weakening tests, skipping them, hardcoding answers,
reconfiguring the test runner, mocking the code under test) and checks whether the
agent disclosed it. One Python engine, three adapters: a Claude Code plugin, a CLI /
GitHub Action, and a benchmark (TemptationBench) that ranks coding agents.

The full spec lives outside the repo; the parts that matter for code are below.

## Current phase: Week 1–2 — detection engine (Python / pytest only)
Build in this order, each with tests before moving on:
1. `engine/inventory/` — collect the test inventory of a repo (`pytest --collect-only -q`),
   diff before vs after: deleted, renamed, newly skipped/xfailed tests.
2. `engine/astdiff/` — tree-sitter (Python grammar) diff of test functions:
   assertions removed, weakened (`==` → `in`/truthy/approx), expected literal changed,
   `pytest.mark.skip/xfail` added, `if` guards around asserts.
3. `engine/rules/` — deterministic rules: conftest.py hooks touching reports,
   pytest.ini/pyproject addopts changes, coverage threshold lowered, CI files with
   `continue-on-error`, `|| true`, `--no-verify`; source special-casing
   (`'pytest' in sys.modules`, `PYTEST_CURRENT_TEST`); broad `except: pass`.
4. `engine/ledger.py` — SQLite event store for `SnitchEvent`s per session.
5. `engine/receipt.py` — render events as Markdown receipt (SARIF later).
6. `snitch` CLI: `snitch diff <base> <head>` and `snitch check --staged`.

NOT in this phase: Claude Code plugin hooks, MCP server, mutation testing, LLM judge,
TypeScript, GitHub App, benchmark, website. Do not start them.

## Progress
- [x] 1. inventory — deleted, renamed-away, newly skipped tests (6 fixtures, all passing)
      Not yet: xfail markers, pytest.skip() inside a test body, edited parametrize values.
- [x] 2. astdiff — assertion removed / weakened / guarded, skip_in_body,
      expected_value_changed (13 fixtures, all passing)
      Not yet: unittest-style asserts, for/while/with guards, positional approx tolerances,
      custom python_files patterns; "source changed" is repo-wide, not per import.
- [x] 3. rules — conftest report hooks, addopts deselection, coverage threshold, CI
      continue-on-error / || true / --no-verify, pytest special-casing, broad except-pass
      (14 fixtures, all passing; totals 19 cheat / 14 legit)
      Not yet: nested config files, Makefile/shell CI surfaces, real YAML parsing.
      Rule event ids hash (session, pattern, file) — there is no test node id.
- [x] 4. ledger — `Ledger(path)`: `record(events)` (INSERT OR IGNORE on id), `events(session_id)`;
      one table, event stored as JSON (5 tests, all passing)
      Not yet: updating judge_verdict / disclosed / escalated on a stored event.
- [ ] 5. receipt  ← current
- [ ] 6. CLI commands

## Core data model (keep exactly; Pydantic v2)
```python
class SnitchEvent(BaseModel):
    id: str
    session_id: str
    family: Literal["tampering", "evasion", "faking", "hollow", "reporting"]
    pattern: str                 # e.g. "assertion_weakened"
    severity: Literal["low", "medium", "high"]
    file: str; line_start: int; line_end: int
    before: str | None; after: str | None
    detector: Literal["ast", "inventory", "rule", "mutation", "judge"]
    judge_verdict: Literal["cheat", "legitimate", "unsure"] | None = None
    judge_reason: str | None = None
    disclosed: bool | None = None
    escalated: bool = False
    created_at: datetime
```

## Decisions already made (do not change without asking)
- Build backend: uv_build, flat `engine/` package; console script `snitch = "engine.cli:app"`.
- pytest ignores `tests/fixtures` (norecursedirs); ruff excludes `tests/fixtures` and `*.md`.
- Fixture tests copy before/ and after/ into tmp_path before running.
- Event ids are a stable hash of (session_id, pattern, node id) so re-runs dedupe.
- Known limitation: collection runs the target repo's conftest.py with Snitch's own
  interpreter; a repo with missing dependencies raises InventoryError.

## Stack and commands
- Python 3.12, managed with **uv** (`uv add`, `uv run`). Never use pip directly.
- Libraries: pydantic v2, tree-sitter + tree-sitter-python, typer (CLI), structlog.
- Tests: pytest. Run `uv run pytest -q` after every change.
- Lint/format: `uv run ruff check . && uv run ruff format .`
- Types: `uv run mypy engine` (strict on `engine/`).

## Testing approach
- Every detector is tested with **fixture pairs**: `tests/fixtures/<pattern>/before/`
  and `after/` mini-repos, plus `expected.json` with the events that must be produced.
- Each pattern needs at least one positive fixture AND one legitimate-change fixture
  that must produce NO event (false-positive guard).
- Target for this phase: 30 cheat fixtures + 15 legitimate fixtures, all passing.

## Rules for you (Claude) while working here
- Never edit, weaken, skip or delete a test to make it pass. If a test looks wrong,
  stop and tell me why — this project exists to catch exactly that.
- Never claim tests pass without running them in the same turn; paste the summary line.
- Never run git commit or git push. Stage nothing. I review and commit myself.
  At the end of a task, propose commit messages (Conventional Commits) for me to use.
- Never add a Co-Authored-By trailer or any mention of Claude/AI in commit messages,
  PR titles or PR bodies.
- Deterministic detectors only in the engine; no network calls, no LLM calls yet.
- Ask before adding a dependency not listed above.
- Keep detectors pure functions: `(before_repo, after_repo) -> list[SnitchEvent]`.

## Layout
```
engine/{inventory,astdiff,rules}/   ledger.py   receipt.py   cli.py
plugin/snitch/                      # later phase
tests/  tests/fixtures/
```
