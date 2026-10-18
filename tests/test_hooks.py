import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest
from typer.testing import CliRunner

from engine import hooks
from engine.cli import app
from engine.ledger import Ledger

runner = CliRunner()


def git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=repo,
        check=True,
        capture_output=True,
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Committed calc.py + test, an uncommitted edit, an untracked file, an ignored file."""
    repo = tmp_path / "repo"
    (repo / "tests").mkdir(parents=True)
    (repo / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    (repo / "tests" / "test_calc.py").write_text("def test_add():\n    assert 1\n")
    (repo / ".gitignore").write_text("build/\n")
    git(repo, "init", "-q")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "init")
    (repo / "calc.py").write_text("def add(a, b):\n    return b + a\n")
    (repo / "notes.py").write_text("x = 1\n")
    (repo / "build").mkdir()
    (repo / "build" / "out.py").write_text("ignored = True\n")
    return repo


def session_start(
    data: Path, cwd: Path, session_id: str = "s1", source: str = "startup"
) -> object:
    payload = {
        "session_id": session_id,
        "cwd": str(cwd),
        "hook_event_name": "SessionStart",
        "source": source,
    }
    return runner.invoke(
        app,
        ["hook", "session-start"],
        input=json.dumps(payload),
        env={"CLAUDE_PLUGIN_DATA": str(data)},
    )


def files(root: Path) -> set[str]:
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}


def test_snapshots_working_tree_without_ignored_files(
    tmp_path: Path, repo: Path
) -> None:
    data = tmp_path / "data"

    result = session_start(data, repo)

    assert result.exit_code == 0, result.output
    baseline = data / "sessions" / "s1" / "baseline"
    assert files(baseline) == {
        ".gitignore",
        "calc.py",
        "notes.py",
        "tests/test_calc.py",
    }
    # the uncommitted edit, not HEAD
    assert "b + a" in (baseline / "calc.py").read_text()


def test_resume_keeps_the_first_baseline(tmp_path: Path, repo: Path) -> None:
    data = tmp_path / "data"
    session_start(data, repo)
    (repo / "tests" / "test_calc.py").write_text("def test_add():\n    pass\n")

    result = session_start(data, repo, source="resume")

    assert result.exit_code == 0, result.output
    baseline = data / "sessions" / "s1" / "baseline"
    assert "assert 1" in (baseline / "tests" / "test_calc.py").read_text()


def test_rejects_session_id_that_is_not_a_plain_id(tmp_path: Path, repo: Path) -> None:
    data = tmp_path / "data"

    result = session_start(data, repo, session_id="../escape")

    assert result.exit_code != 0
    assert "invalid session_id" in result.stderr
    assert not (tmp_path / "escape").exists()
    assert not data.exists() or files(data) == set()


def test_outside_a_git_repo_does_nothing(tmp_path: Path) -> None:
    data = tmp_path / "data"
    plain = tmp_path / "plain"
    plain.mkdir()

    result = session_start(data, plain)

    assert result.exit_code == 0
    assert "not a git repository" in result.stderr
    assert not (data / "sessions" / "s1").exists()


FIXTURES = Path(__file__).parent / "fixtures"


def post_tool(data: Path, cwd: Path, mode: str | None = None) -> object:
    payload = {
        "session_id": "s1",
        "cwd": str(cwd),
        "hook_event_name": "PostToolUse",
        "tool_name": "Edit",
        "tool_input": {"file_path": str(cwd / "test_calc.py")},
    }
    env = {"CLAUDE_PLUGIN_DATA": str(data)}
    if mode:
        env["CLAUDE_PLUGIN_OPTION_MODE"] = mode
    return runner.invoke(app, ["hook", "post-tool"], input=json.dumps(payload), env=env)


def agent_session(tmp_path: Path, fixture: str) -> tuple[Path, Path]:
    """Repo committed at the fixture's before/, baseline taken, then the agent's
    edit (the fixture's after/) applied to the work tree. Returns (data, repo)."""
    repo = shutil.copytree(FIXTURES / fixture / "before", tmp_path / "repo")
    git(repo, "init", "-q")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "before")
    data = tmp_path / "data"
    assert session_start(data, repo).exit_code == 0
    shutil.copytree(FIXTURES / fixture / "after", repo, dirs_exist_ok=True)
    return data, repo


def recorded(data: Path) -> list[str]:
    ledger = Ledger(data / "ledger.db")
    try:
        return [e.pattern for e in ledger.events("s1")]
    finally:
        ledger.close()


def test_warn_tells_the_agent_and_records(tmp_path: Path) -> None:
    data, repo = agent_session(tmp_path, "assertion_weakened_in")

    result = post_tool(data, repo)

    assert result.exit_code == 0, result.output
    context = json.loads(result.stdout)["hookSpecificOutput"]
    assert context["hookEventName"] == "PostToolUse"
    assert "assertion_weakened" in context["additionalContext"]
    assert "test_calc.py:9" in context["additionalContext"]
    assert recorded(data) == ["assertion_weakened"]


def test_same_event_is_reported_once(tmp_path: Path) -> None:
    data, repo = agent_session(tmp_path, "assertion_weakened_in")
    post_tool(data, repo)
    (repo / "notes.txt").write_text("tree changed, cheat unchanged\n")

    result = post_tool(data, repo)

    assert result.exit_code == 0, result.output
    assert result.stdout == ""
    assert recorded(data) == ["assertion_weakened"]


def test_observe_records_without_telling(tmp_path: Path) -> None:
    data, repo = agent_session(tmp_path, "assertion_weakened_in")

    result = post_tool(data, repo, mode="observe")

    assert result.exit_code == 0, result.output
    assert result.stdout == ""
    assert recorded(data) == ["assertion_weakened"]


def test_legit_edit_is_silent(tmp_path: Path) -> None:
    data, repo = agent_session(tmp_path, "legit_assert_added")

    result = post_tool(data, repo)

    assert result.exit_code == 0, result.output
    assert result.stdout == ""
    assert recorded(data) == []


def test_unchanged_tree_skips_the_detectors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data, repo = agent_session(tmp_path, "legit_assert_added")
    post_tool(data, repo)

    def fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("detectors ran on an unchanged tree")

    monkeypatch.setattr(hooks, "run_detectors", fail)
    result = post_tool(data, repo)

    assert result.exit_code == 0, result.output


def test_without_a_baseline_does_nothing(tmp_path: Path, repo: Path) -> None:
    data = tmp_path / "data"

    result = post_tool(data, repo)

    assert result.exit_code == 0, result.output
    assert result.stdout == ""
    assert not (data / "ledger.db").exists()


def test_hook_errors_exit_1(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["hook", "post-tool"],
        input="not json",
        env={"CLAUDE_PLUGIN_DATA": str(tmp_path)},
    )

    assert result.exit_code == 1


def test_escalated_file_is_not_nagged_about(tmp_path: Path) -> None:
    data, repo = agent_session(tmp_path, "assertion_weakened_in")
    ledger = Ledger(data / "ledger.db")
    ledger.escalate("s1", "test_calc.py::test_divide", "spec changed", "")
    ledger.close()

    result = post_tool(data, repo)

    assert result.exit_code == 0, result.output
    assert result.stdout == ""
    assert recorded(data) == ["assertion_weakened"]


def test_ignores_a_different_repo_than_the_baseline(tmp_path: Path) -> None:
    data, _ = agent_session(tmp_path, "assertion_weakened_in")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    git(elsewhere, "init", "-q")

    result = post_tool(data, elsewhere)

    assert result.exit_code == 0, result.output
    assert result.stdout == ""
    assert recorded(data) == []


def stop(
    data: Path,
    cwd: Path,
    message: str,
    mode: str | None = None,
    active: bool = False,
) -> object:
    payload = {
        "session_id": "s1",
        "cwd": str(cwd),
        "hook_event_name": "Stop",
        "stop_hook_active": active,
        "last_assistant_message": message,
    }
    env = {"CLAUDE_PLUGIN_DATA": str(data)}
    if mode:
        env["CLAUDE_PLUGIN_OPTION_MODE"] = mode
    return runner.invoke(app, ["hook", "stop"], input=json.dumps(payload), env=env)


def disclosed(data: Path) -> list[bool | None]:
    ledger = Ledger(data / "ledger.db")
    try:
        return [e.disclosed for e in ledger.events("s1")]
    finally:
        ledger.close()


SILENT = "Done: all tests pass now."
HONEST = "I changed the assertion in test_calc.py; the old expectation was wrong."


def test_stop_warn_tells_the_user_without_blocking(tmp_path: Path) -> None:
    data, repo = agent_session(tmp_path, "assertion_weakened_in")
    post_tool(data, repo)

    result = stop(data, repo, SILENT)

    assert result.exit_code == 0, result.output
    out = json.loads(result.stdout)
    assert "decision" not in out
    assert "assertion_weakened" in out["systemMessage"]
    assert disclosed(data) == [False]


def test_stop_enforce_blocks_an_undisclosed_cheat(tmp_path: Path) -> None:
    data, repo = agent_session(tmp_path, "assertion_weakened_in")
    post_tool(data, repo)

    result = stop(data, repo, SILENT, mode="enforce")

    out = json.loads(result.stdout)
    assert out["decision"] == "block"
    assert "test_calc.py:9" in out["reason"]
    assert "escalate" in out["reason"]


def test_stop_enforce_never_blocks_twice_in_a_row(tmp_path: Path) -> None:
    data, repo = agent_session(tmp_path, "assertion_weakened_in")
    post_tool(data, repo)

    result = stop(data, repo, SILENT, mode="enforce", active=True)

    out = json.loads(result.stdout)
    assert "decision" not in out
    assert "assertion_weakened" in out["systemMessage"]


def test_stop_accepts_a_disclosed_change(tmp_path: Path) -> None:
    data, repo = agent_session(tmp_path, "assertion_weakened_in")
    post_tool(data, repo)

    result = stop(data, repo, HONEST, mode="enforce")

    assert result.exit_code == 0, result.output
    assert result.stdout == ""
    assert disclosed(data) == [True]


def test_stop_accepts_an_escalated_test(tmp_path: Path) -> None:
    data, repo = agent_session(tmp_path, "assertion_weakened_in")
    ledger = Ledger(data / "ledger.db")
    ledger.escalate("s1", "test_calc.py", "spec says 5 or 6", "")
    ledger.close()

    result = stop(data, repo, SILENT, mode="enforce")

    assert result.exit_code == 0, result.output
    assert result.stdout == ""


def test_stop_catches_a_cheat_post_tool_never_saw(tmp_path: Path) -> None:
    data, repo = agent_session(tmp_path, "assertion_weakened_in")

    result = stop(data, repo, SILENT, mode="enforce")

    assert json.loads(result.stdout)["decision"] == "block"
    assert recorded(data) == ["assertion_weakened"]


def test_stop_observe_records_silently(tmp_path: Path) -> None:
    data, repo = agent_session(tmp_path, "assertion_weakened_in")

    result = stop(data, repo, SILENT, mode="observe")

    assert result.exit_code == 0, result.output
    assert result.stdout == ""
    assert disclosed(data) == [False]


def test_stop_on_a_clean_session_is_silent(tmp_path: Path) -> None:
    data, repo = agent_session(tmp_path, "legit_assert_added")

    result = stop(data, repo, SILENT, mode="enforce")

    assert result.exit_code == 0, result.output
    assert result.stdout == ""


def test_session_start_drops_stale_sessions(tmp_path: Path, repo: Path) -> None:
    data = tmp_path / "data"
    for session_id in ("old", "recent"):
        session_start(data, repo, session_id=session_id)
    month_ago = time.time() - 30 * 24 * 3600
    for path in (data / "sessions" / "old").rglob("*"):
        os.utime(path, (month_ago, month_ago))
    os.utime(data / "sessions" / "old", (month_ago, month_ago))

    session_start(data, repo, session_id="new")

    assert sorted(p.name for p in (data / "sessions").iterdir()) == ["new", "recent"]


def pre_tool(
    data: Path, cwd: Path, tool: str, tool_input: dict[str, str], mode: str = "enforce"
) -> object:
    payload = {
        "session_id": "s1",
        "cwd": str(cwd),
        "hook_event_name": "PreToolUse",
        "tool_name": tool,
        "tool_input": tool_input,
    }
    env = {"CLAUDE_PLUGIN_DATA": str(data), "CLAUDE_PLUGIN_OPTION_MODE": mode}
    return runner.invoke(app, ["hook", "pre-tool"], input=json.dumps(payload), env=env)


def denied(result: object) -> str | None:
    """The deny reason, or None when the hook let the call through."""
    assert result.exit_code == 0, result.output
    if not result.output.strip():
        return None
    out = json.loads(result.output)["hookSpecificOutput"]
    assert out["hookEventName"] == "PreToolUse"
    assert out["permissionDecision"] == "deny"
    return str(out["permissionDecisionReason"])


@pytest.mark.parametrize("tool", ["Edit", "Write", "MultiEdit"])
def test_enforce_denies_edits_to_frozen_paths(
    tmp_path: Path, repo: Path, tool: str
) -> None:
    (repo / ".snitch.toml").write_text('frozen = ["tests/**", "pytest.ini"]\n')
    target = {"file_path": str(repo / "tests" / "test_calc.py")}

    reason = denied(pre_tool(tmp_path / "data", repo, tool, target))

    assert reason is not None
    assert "tests/test_calc.py" in reason and "escalate" in reason


def test_enforce_allows_edits_outside_frozen_paths(tmp_path: Path, repo: Path) -> None:
    (repo / ".snitch.toml").write_text('frozen = ["tests/**"]\n')
    data = tmp_path / "data"
    for path in (repo / "calc.py", tmp_path / "elsewhere" / "tests" / "test_x.py"):
        assert denied(pre_tool(data, repo, "Edit", {"file_path": str(path)})) is None


def test_without_snitch_toml_nothing_is_frozen(tmp_path: Path, repo: Path) -> None:
    target = {"file_path": str(repo / "tests" / "test_calc.py")}
    assert denied(pre_tool(tmp_path / "data", repo, "Edit", target)) is None


@pytest.mark.parametrize("mode", ["observe", "warn"])
def test_gate_only_blocks_in_enforce(tmp_path: Path, repo: Path, mode: str) -> None:
    (repo / ".snitch.toml").write_text('frozen = ["tests/**"]\n')
    data = tmp_path / "data"
    target = {"file_path": str(repo / "tests" / "test_calc.py")}
    command = {"command": "git commit --no-verify -m x"}
    assert denied(pre_tool(data, repo, "Edit", target, mode)) is None
    assert denied(pre_tool(data, repo, "Bash", command, mode)) is None


@pytest.mark.parametrize(
    "command",
    [
        "sed -i 's/1/0/' tests/test_calc.py",
        "cd tests && sed -i.bak -e 's/1/0/' test_calc.py",
        "sed -Ei 's/1/0/' tests/test_calc.py; pytest",
        "sed --in-place 's/1/0/' tests/calc_test.py",
        "git commit --no-verify -m wip",
        "git push --no-verify",
    ],
)
def test_bash_gate_denies_in_place_test_edits_and_no_verify(
    tmp_path: Path, repo: Path, command: str
) -> None:
    reason = denied(pre_tool(tmp_path / "data", repo, "Bash", {"command": command}))
    assert reason is not None and "escalate" in reason


@pytest.mark.parametrize(
    "command",
    [
        "sed -i 's/a/b/' calc.py",
        "sed -n '1,5p' tests/test_calc.py",
        "echo --no-verify",
        "git commit -m 'explain --no-verify in docs'",
        "uv run pytest -q",
    ],
)
def test_bash_gate_allows_other_commands(
    tmp_path: Path, repo: Path, command: str
) -> None:
    assert (
        denied(pre_tool(tmp_path / "data", repo, "Bash", {"command": command})) is None
    )


def test_bash_gate_covers_frozen_non_test_files(tmp_path: Path, repo: Path) -> None:
    (repo / ".snitch.toml").write_text('frozen = ["pytest.ini"]\n')
    command = {"command": "sed -i 's/-q/-q -k add/' pytest.ini"}
    assert denied(pre_tool(tmp_path / "data", repo, "Bash", command)) is not None


def test_malformed_snitch_toml_is_a_hook_error(tmp_path: Path, repo: Path) -> None:
    (repo / ".snitch.toml").write_text('frozen = "tests/**"\n')
    target = {"file_path": str(repo / "calc.py")}
    result = pre_tool(tmp_path / "data", repo, "Edit", target)
    assert result.exit_code == 1
    assert ".snitch.toml" in result.output


@pytest.mark.parametrize(
    ("value", "mode"),
    [(None, "warn"), ("", "warn"), ("observe", "observe"), (" Enforce\n", "enforce")],
)
def test_mode_comes_from_the_plugin_option(
    monkeypatch: pytest.MonkeyPatch, value: str | None, mode: str
) -> None:
    monkeypatch.delenv("CLAUDE_PLUGIN_OPTION_MODE", raising=False)
    if value is not None:
        monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_MODE", value)
    assert hooks._mode() == mode


def test_unknown_mode_falls_back_to_warn_and_says_so(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_MODE", "strict")
    assert hooks._mode() == "warn"
    assert "strict" in capsys.readouterr().err
