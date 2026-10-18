import shutil
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from engine.cli import app
from engine.ledger import Ledger

FIXTURES = Path(__file__).parent / "fixtures"
WEAKENED_ROW = "| high | tampering | assertion_weakened | test_calc.py:9 | ast |"
runner = CliRunner()


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def repo_from(tmp_path: Path, before: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A throwaway git repo whose first commit is `before`; cwd is moved into it."""
    repo = shutil.copytree(before, tmp_path / "repo")
    git(repo, "init", "-q")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "before")
    monkeypatch.chdir(repo)
    return repo


def commit_after(repo: Path, after: Path) -> None:
    shutil.copytree(after, repo, dirs_exist_ok=True)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "after")


def test_diff_reports_cheat(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fixture = FIXTURES / "assertion_weakened_in"
    repo = repo_from(tmp_path, fixture / "before", monkeypatch)
    commit_after(repo, fixture / "after")

    result = runner.invoke(app, ["diff", "HEAD~1", "HEAD"])

    assert result.exit_code == 1
    assert WEAKENED_ROW in result.stdout


def test_diff_clean(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fixture = FIXTURES / "legit_variable_renamed"
    repo = repo_from(tmp_path, fixture / "before", monkeypatch)
    commit_after(repo, fixture / "after")

    result = runner.invoke(app, ["diff", "HEAD~1", "HEAD"])

    assert result.exit_code == 0
    assert "No integrity issues found." in result.stdout


def test_check_staged_sees_only_staged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = FIXTURES / "assertion_weakened_in"
    repo = repo_from(tmp_path, fixture / "before", monkeypatch)
    shutil.copytree(fixture / "after", repo, dirs_exist_ok=True)

    unstaged = runner.invoke(app, ["check", "--staged"])
    git(repo, "add", "-A")
    staged = runner.invoke(app, ["check", "--staged"])

    assert unstaged.exit_code == 0
    assert "No integrity issues found." in unstaged.stdout
    assert staged.exit_code == 1
    assert WEAKENED_ROW in staged.stdout


def test_rerun_adds_no_ledger_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = FIXTURES / "assertion_weakened_in"
    repo = repo_from(tmp_path, fixture / "before", monkeypatch)
    commit_after(repo, fixture / "after")
    session = (
        f"diff:{git(repo, 'rev-parse', 'HEAD~1')}..{git(repo, 'rev-parse', 'HEAD')}"
    )

    runner.invoke(app, ["diff", "HEAD~1", "HEAD"])
    runner.invoke(app, ["diff", "HEAD~1", "HEAD"])

    ledger = Ledger(repo / ".git" / "snitch" / "ledger.db")
    assert [e.pattern for e in ledger.events(session)] == ["assertion_weakened"]
    ledger.close()


def test_collection_failure_warns_and_continues(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = FIXTURES / "assertion_weakened_in"
    before = shutil.copytree(fixture / "before", tmp_path / "before")
    after = shutil.copytree(fixture / "after", tmp_path / "after")
    for side in (before, after):
        (side / "conftest.py").write_text("import snitch_missing_dependency\n")
    repo = repo_from(tmp_path, before, monkeypatch)
    commit_after(repo, after)

    result = runner.invoke(app, ["diff", "HEAD~1", "HEAD"])

    assert result.exit_code == 1
    assert "inventory" in result.stderr
    assert WEAKENED_ROW in result.stdout


def test_unknown_ref_is_a_usage_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_from(tmp_path, FIXTURES / "assertion_weakened_in" / "before", monkeypatch)

    result = runner.invoke(app, ["diff", "no-such-ref", "HEAD"])

    assert result.exit_code == 2
    assert "no-such-ref" in result.stderr
