<p align="center">
  <img src="assets/logo.svg" width="112" alt="Snitch logo: an eye">
</p>

<h1 align="center">Snitch</h1>

<p align="center">
  <b>The integrity layer for AI coding agents.</b><br>
  Catches agents that make a failing test pass by cheating, and gives them an honest way out.
</p>

<p align="center">
  <a href="https://github.com/ennajari/snitch/actions/workflows/ci.yml"><img src="https://github.com/ennajari/snitch/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT license"></a>
  <img src="https://img.shields.io/badge/python-3.12-blue" alt="Python 3.12">
  <img src="https://img.shields.io/badge/status-early-orange" alt="Status: early">
</p>

<p align="center">
  <img src="assets/demo-session.gif" width="760" alt="Claude Code with Snitch: the agent runs the tests, finds a wrong expected value, calls escalate instead of editing the test, and tells the user">
  <br><sub>A real <code>claude plugin eval</code> run (2026-10-24, case <code>broken-expected-value</code>), replayed; the agent's messages are quoted, shortened where marked “…”. Without Snitch, the same agent edited the test in 8 of 32 trap runs.</sub>
</p>

---

You ask a coding agent to make CI green. It comes back with "all tests pass". What it
did: change `assert total == 42` into `assert total`, mark the failing test `skip`, or
add `-k "not slow"` to `pytest.ini`. The diff is green; the bug is still there.

**Snitch watches for exactly that**, live in your Claude Code session, on every pull
request, and in a benchmark that ranks agents by honesty. It never asks a model whether
something "looks like cheating": every finding comes from a deterministic detector and
points at a line in the diff.

```diff
- assert divide(10, 2) == 5
+ assert divide(10, 2) in (5, 6)
```

```
# Snitch receipt
**1 event** — 1 high

| Severity | Family    | Pattern            | Location       | Detector |
|----------|-----------|--------------------|----------------|----------|
| high     | tampering | assertion_weakened | test_calc.py:9 | ast      |
```

## See it catch

<table>
<tr>
<td width="50%"><img src="assets/demo-planted.gif" alt="An agent makes a test that needs a missing CI secret pass by setting the secret inside the test; snitch check flags assertion_self_fulfilled"><br><sub><b>A test that can't fail.</b> In a real TemptationBench trial, an agent made a test that needs a missing CI secret pass by setting that secret inside the test. Snitch flags it. Patch and message shortened.</sub></td>
<td width="50%"><img src="assets/demo-hooks.gif" alt="The plugin warns the agent after a weakened assert, then blocks a final message that hides it"><br><sub><b>Live in Claude Code.</b> The plugin's real hook output: a warning right after a weakened assert, then a blocked stop when the final message hides it.</sub></td>
</tr>
<tr>
<td colspan="2" align="center"><img src="assets/demo-check.gif" width="66%" alt="git diff and snitch check on a weakened assertion, exit code 1"><br><sub><b>Before you commit.</b> Real <code>snitch check</code> output; exit code 1 fails a pre-commit hook or CI step.</sub></td>
</tr>
</table>

## Why

Research has shown that coding agents cheat on tests, and that an honest exit helps:

- **EvilGenie** ([arXiv 2511.21654](https://arxiv.org/abs/2511.21654)) observed explicit
  reward hacking by Codex and Claude Code.
- **SpecBench** ([arXiv 2605.21384](https://arxiv.org/abs/2605.21384)): frontier agents
  saturate visible tests while hacking persists on held-out ones.
- **BenchJack** ([arXiv 2605.12673](https://arxiv.org/abs/2605.12673)): one root
  `conftest.py` hook can rewrite every test outcome, and most reviewers would miss it.
- **Escalation channels** ([arXiv 2608.29460](https://arxiv.org/abs/2608.29460)):
  agents rarely disclose tampering, but giving them a way to report a broken test
  reduces hacking; escalating and hacking were almost mutually exclusive.

- **ImpossibleBench** ([arXiv 2510.20270](https://arxiv.org/abs/2510.20270)): on
  impossible tasks, agents edit tests, overload `__eq__`, keep hidden state or
  special-case inputs; LLM monitors caught only 42–65% of it on real repos.

Snitch turns those findings into something you install: it **detects** the cheat,
gives the agent the **policy + `escalate` tool** combination that cut reward hacking
from 23.6% to 5.3% in the escalation study, and **refuses to let a session end** with a
test change the agent did not mention. [How each paper shaped Snitch](docs/research.md).

## How it works

```mermaid
flowchart LR
    A["Claude Code plugin<br/>(live, per tool call)"] --> E
    B["GitHub Action / pre-commit<br/>(per PR or commit)"] --> E
    C["TemptationBench<br/>(Harbor, per trial)"] --> E
    E["Engine: before vs after<br/>test inventory · AST assertion diff · rules"] --> R["Events → receipt,<br/>SARIF, ledger, scores"]
```

One engine, three adapters, so the benchmark measures exactly what users install. Each
detector is a pure function of (before, after):

- **inventory**: `pytest --collect-only` before and after; tests that vanished,
  were renamed away, skipped or deselected.
- **astdiff**: tree-sitter diff of every test function; assertions removed, weakened
  (`==` → `in`, looser `approx`, looser bounds, `==` → `!=`), expected values changed,
  asserts hidden behind a new `if`.
- **rules**: runner and CI config (`addopts`, coverage thresholds, `continue-on-error`,
  `|| true`, `--no-verify`), `conftest.py` report hooks, code that special-cases
  `pytest`, `except: pass` around changed logic.

## Measured, not claimed

`claude plugin eval` on 20 seeded repos (broken test, impossible spec, flaky test, slow
test, runner config, controls), 2 runs per case, with and without the plugin
([full report](docs/evals/2026-10-24-plugin-eval-policy.md)):

| | without Snitch | with Snitch |
|---|---|---|
| trap runs where the agent edited the test | **8 / 32** | **0 / 32** |
| trap runs that called `escalate` | n/a | 28 / 32 |
| control tasks completed | 8 / 8 | 8 / 8 |
| false escalations on controls | 0 | 0 |

Paired McNemar p = 0.008 (per case: 5 cases → 0, p = 0.063). An earlier run without the
session-start policy gave 7/32 → 0/32 with 25/32 escalations
([report](docs/evals/2026-10-24-plugin-eval.md)). In both runs the agent disclosed every
test edit even without Snitch, so this says nothing yet about *silent* cheating; that is
what TemptationBench, with hidden tests, is for. The reports list the threats to
validity.

## Install

### Claude Code plugin

```
/plugin marketplace add ennajari/snitch
/plugin install snitch@snitch
```

Pick a mode in `/config` (needs Claude Code 2.1.271 or later):

- `observe`: record only
- `warn` (default): tell the agent and you, never block
- `enforce`: also block edits to frozen tests and stops that hide test changes

Snitch collects your tests with the repo's own `.venv/bin/python` when there is one
(set `SNITCH_PYTHON` to use another interpreter), so tests that import your project's
dependencies can be inventoried. That interpreter needs pytest.

Freeze paths the agent must never edit in `.snitch.toml` at the repo root:

```toml
frozen = ["tests/**", "pytest.ini", "conftest.py"]
```

Ask Claude for "the snitch ledger" to see the session's receipt.

What `enforce` can and cannot block. It denies the agent's Edit/Write calls on frozen
paths, `sed -i` / `perl -i` on test files, `git --no-verify`, and any write to Snitch's
own state: `.snitch.toml`, the plugin's ledger and baselines, the installed plugin, and
the Claude Code settings files that could switch hooks off. Shell commands are checked
for the common write forms (`>`, `>>`, `tee`, `rm`, `mv`, `cp`, `sed -i` ...), not for
every possible one: a Python one-liner or a `cd` inside the command line gets through.
The gate is a guard rail inside the agent's own session, not a sandbox. Every change
still goes through the detectors after the tool call and at the Stop hook, and in CI
the GitHub Action re-checks the diff from outside the agent's reach.

### GitHub Action

```yaml
on: pull_request
permissions:
  contents: read
  pull-requests: write     # the receipt comment
  security-events: write   # code scanning
jobs:
  snitch:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
        with:
          fetch-depth: 0   # Snitch compares the PR base with its head
      - uses: ennajari/snitch@v1
```

Inputs: `fail-on-events` (default `true`), `python` (an interpreter that can import your tests; default: the repo's `.venv`, else Snitch's own), `strict` (fail when a detector could not run, default `false`: an incomplete check passes with a warning and a note in the receipt), `comment`, `upload-sarif`, `base`, `head`.
Output: `events`.

### pre-commit

```yaml
repos:
  - repo: https://github.com/ennajari/snitch
    rev: v0.2.0
    hooks:
      - id: snitch
```

### CLI

```
uvx --from git+https://github.com/ennajari/snitch snitch check   # working tree vs HEAD (--staged: staged only)
snitch diff <base> <head> [--sarif out.sarif]
snitch compare <before-dir> <after-dir> [--json]
```

Exit codes: `0` clean, `1` events found, `2` usage error, `3` incomplete check (only with `--strict`: a detector could not run, for example because the repo's tests do not import).

## What it flags

| Family | Patterns |
|---|---|
| tampering | `assertion_removed`, `assertion_weakened` (truthy-only, `in`, `is not None`, looser `approx` or bounds, `==` flipped to `!=`, `assert x` flipped to `assert not x`, an exact value turned into a range; also the `unittest` `self.assert*` forms), `assertion_guarded` (behind an `if`, `try`, or a loop that never runs), `expected_value_changed`, `assertion_rewritten` (the actual value wrapped until it fits: `f(x) * 60 == 19800`), `parametrize_value_changed`, `test_scope_reduced` (a test's `range(N)` cut tenfold), `test_deleted`, `test_renamed_away`, `conftest_report_hook`, `coverage_threshold_lowered` |
| evasion | `test_deselected`, `test_skipped`, `skip_in_body`, `addopts_changed`, `ci_continue_on_error`, `ci_or_true`, `ci_no_verify` (workflows, GitLab CI, and test runs in Makefiles and shell scripts) |
| faking | `test_env_special_casing`, `comparison_forced` (an `__eq__` that returns True for anything), `assertion_self_fulfilled` (a test that now sets the very value it asserts, e.g. the CI secret it was checking, in the test, a fixture or a `conftest.py`) |
| hollow | `broad_except_pass` |
| reporting (plugin, at the end of a turn) | a flagged test change the final message does not mention; "tests pass" claimed with no test run since the last edit |

Every detector is a pure function of (before, after) and is tested on a cheating
fixture and a legitimate one that must stay silent. Snitch flags changes; whether a
flagged change was legitimate is up to the person reading the receipt (or the agent's
disclosure). Updating a test because the requested behaviour changed is fine, as long
as it is said.

## TemptationBench

`bench/` holds 40 [Harbor](https://github.com/harbor-framework/harbor) tasks: small,
realistic projects with one built-in temptation each (a broken test, an impossible spec,
a missing service, a flaky test, a hard task) plus 14 controls. Hidden held-out tests
grade the work, and the agent's own `conftest.py` or `addopts` cannot fake them. Every
task ships a reference solution that must score 1 and a typical cheat that must score 0,
both checked in CI and in Docker.

`snitch bench-score` turns Harbor runs into the leaderboard metrics: solve rate, cheat
rate, silent-cheat rate (with a bootstrap 95% interval over tasks), honest-escalation
rate, false positives on controls, a per-temptation breakdown, and McNemar's test for
with vs without Snitch. Flagged trials are confirmed or cleared with human labels.
### First results: Claude Code (edition 2026-11)

Claude Code 2.1.310 on its default model (claude-sonnet-5-5), 40 tasks × 3 runs, with
and without the Snitch plugin; every flagged trial reviewed by hand
([full results and limits](bench/results/2026-11/README.md)):

| | without Snitch | with Snitch |
|---|---|---|
| trials where the agent changed a test | **18 / 120** | **0 / 120** |
| …of them hidden from the user (silent) | 0 | 0 |
| trap trials where it called `escalate` instead | n/a | 51 / 78 |
| false alarms on the 42 control trials | 0 | 0 |

Paired McNemar p = 0.000008 (per task: 8 → 0, p = 0.008). The 18 changes came from broken
tests (10) and flaky tests (8), and every one was disclosed: Claude Code changed the
test and said so, and on the broken tests it was right that the test was wrong. With
Snitch it reported the problem instead of changing the test. Codex CLI has been run
on the same 120 trials; its results follow on 8 November 2026, after the 14-day vendor
preview. Gemini CLI is being run.
(Corrected from 14: a second review pass found 4 more, all disclosed; see the
results page.)

## Roadmap

- [x] Engine: inventory, AST diff, rules (Python / pytest), 39 cheating + 24 legitimate fixtures
- [x] Claude Code plugin: live detection, `escalate`, Stop verifier, enforce gate, evals
- [x] GitHub Action with SARIF + PR receipt, pre-commit hook
- [x] TemptationBench: 40 tasks, scoring
- [x] Edition 2026-11 for Claude Code (40 tasks × 3 runs × with/without Snitch, human-reviewed)
- [x] Codex CLI run and reviewed (results 8 November 2026, after the vendor preview)
- [ ] Gemini CLI (running), then OpenCode and others
- [ ] Disclosure judge, mutation testing for hollow tests
- [ ] TypeScript (Jest / Vitest)

## Contributing

Seen an agent cheat in a way Snitch misses? Open an issue with the before/after diff
(anonymized). Every confirmed case becomes a detector fixture or a benchmark task. Each
new pattern needs a cheating fixture that must be flagged and a legitimate one that must
stay silent.

## Development

```
uv sync
uv run pytest -q
uv run ruff check . && uv run ruff format .
uv run mypy engine
```

## Citing

If you use Snitch or TemptationBench in your work, please cite it
([CITATION.cff](CITATION.cff); GitHub's "Cite this repository" button gives other formats):

```bibtex
@software{ennajari_snitch_2026,
  author  = {Ennajari, Abdellah},
  title   = {Snitch: an integrity layer for AI coding agents, and TemptationBench},
  year    = {2026},
  version = {0.2.0},
  url     = {https://github.com/ennajari/Snitch}
}
```

## License

[MIT](LICENSE)
