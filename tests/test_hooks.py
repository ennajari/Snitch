import json
import shutil
import subprocess
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
