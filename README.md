# Snitch

**The integrity layer for AI coding agents.** Snitch catches agents that make a
failing test pass by cheating (weakening, skipping or deleting the test, reconfiguring
the test runner, special-casing the code under test) and checks whether the agent
said so. It also gives the agent an honest way out: an `escalate` tool to report a test
it believes is wrong, instead of quietly changing it.

One deterministic Python engine, three ways to use it:

| | Where it runs | What it does |
|---|---|---|
| **Claude Code plugin** | live, in your session | warns (or blocks) as soon as a test is weakened; refuses to let the session end with an undisclosed change |
| **GitHub Action** | every pull request, any agent or human | posts an integrity receipt on the PR and flags lines in code scanning |
| **pre-commit hook / CLI** | your machine, before each commit | blocks commits that weaken tests |

Status: early, Python / pytest only.

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

Freeze paths the agent must never edit in `.snitch.toml` at the repo root:

```toml
frozen = ["tests/**", "pytest.ini", "conftest.py"]
```

Ask Claude for "the snitch ledger" to see the session's receipt.

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
      - uses: ennajari/snitch@master
```

Inputs: `fail-on-events` (default `true`), `comment`, `upload-sarif`, `base`, `head`.
Output: `events`.

### pre-commit

```yaml
repos:
  - repo: https://github.com/ennajari/snitch
    rev: master
    hooks:
      - id: snitch
```

### CLI

```
uvx --from git+https://github.com/ennajari/snitch snitch check --staged
snitch diff <base> <head> [--sarif out.sarif]
snitch compare <before-dir> <after-dir> [--json]
```

Exit codes: `0` clean, `1` events found, `2` usage error.

## What it flags

| Family | Patterns |
|---|---|
| tampering | `assertion_removed`, `assertion_weakened` (truthy-only, `in`, `is not None`, looser `approx` or bounds, `==` flipped to `!=`), `expected_value_changed`, `parametrize_value_changed`, `assertion_guarded`, `test_deleted`, `test_renamed_away`, `conftest_report_hook`, `coverage_threshold_lowered` |
| evasion | `test_deselected`, `test_skipped`, `skip_in_body`, `addopts_changed`, `ci_continue_on_error`, `ci_or_true`, `ci_no_verify` |
| faking | `test_env_special_casing` |
| hollow | `broad_except_pass` |

Every detector is a pure function of (before, after) and is tested on a cheating
fixture and a legitimate one that must stay silent. Snitch flags changes; whether a
flagged change was legitimate is up to the person reading the receipt (or the agent's
disclosure). Updating a test because the requested behaviour changed is fine, as long
as it is said.

## TemptationBench

`bench/` holds 40 Harbor tasks: realistic small projects with one built-in temptation
each (a broken test, an impossible spec, a missing service, a flaky test, a hard task)
plus controls. Hidden tests grade the agent's work; `snitch bench-score` turns Harbor
runs into cheat, silent-cheat and honest-escalation rates, with and without Snitch.
No results are published yet.

## Development

```
uv sync
uv run pytest -q
uv run ruff check . && uv run ruff format .
uv run mypy engine
```
