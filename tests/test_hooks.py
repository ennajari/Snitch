import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from engine.cli import app

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
