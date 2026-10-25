import json
import shutil
import sys
from pathlib import Path

import pytest

from engine.inventory import diff_inventory
from engine.inventory.collect import InventoryError, collect, find_python

FIXTURES = Path(__file__).parent / "fixtures"
COMPARED = {
    "family",
    "pattern",
    "severity",
    "file",
    "line_start",
    "line_end",
    "before",
    "after",
    "detector",
}


@pytest.mark.parametrize(
    "name",
    [
        "test_deleted",
        "test_skipped",
        "test_renamed_away",
        "legit_test_renamed",
        "legit_test_moved",
        "legit_skip_unchanged",
        "test_skipped_if",
        "parametrize_case_removed",
        "test_xfailed",
        "parametrize_value_changed",
        "legit_parametrize_case_added",
        "legit_parametrize_value_fixed",
        "test_deselected",
        "test_deleted_with_cov_addopts",
    ],
)
def test_inventory_fixture(name: str, tmp_path: Path) -> None:
    # Copy out of the repo so collection ignores our own pytest config and leaves no caches.
    before = shutil.copytree(FIXTURES / name / "before", tmp_path / "before")
    after = shutil.copytree(FIXTURES / name / "after", tmp_path / "after")
    expected = json.loads((FIXTURES / name / "expected.json").read_text())

    events = [e.model_dump(include=COMPARED) for e in diff_inventory(before, after)]

    assert events == expected


def test_cached_collection_is_reused(tmp_path: Path) -> None:
    repo = shutil.copytree(FIXTURES / "test_deleted" / "before", tmp_path / "repo")
    cache = tmp_path / "inventory.json"
    first = collect(repo, cache)
    assert first and cache.is_file()

    # a second call must not collect again: the deleted tests are still listed
    shutil.rmtree(repo)
    assert collect(repo, cache) == first


def fake_venv(repo: Path, script: str) -> Path:
    """A repo-local .venv/bin/python: a shell wrapper standing in for the repo's env."""
    python = repo / ".venv" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text(f"#!/bin/sh\n{script}\n")
    python.chmod(0o755)
    return python


def repo_needing(tmp_path: Path, package: str) -> Path:
    """A repo whose test imports a package Snitch's own environment does not have."""
    repo = tmp_path / "repo"
    (repo / "tests").mkdir(parents=True)
    (repo / "tests" / "test_a.py").write_text(
        f"import {package}\n\n\ndef test_a():\n    assert {package}.VALUE == 1\n"
    )
    return repo


def test_python_comes_from_env_then_the_repo_venv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("SNITCH_PYTHON", raising=False)
    assert find_python(tmp_path) is None
    venv = fake_venv(tmp_path, "exit 1")
    assert find_python(tmp_path) == str(venv)
    monkeypatch.setenv("SNITCH_PYTHON", "/opt/py/bin/python")
    assert find_python(tmp_path) == "/opt/py/bin/python"


@pytest.mark.skipif(sys.platform == "win32", reason="shell wrapper")
def test_collects_with_the_repos_own_interpreter(tmp_path: Path) -> None:
    repo = repo_needing(tmp_path, "only_in_repo_env")
    site = tmp_path / "site"
    site.mkdir()
    (site / "only_in_repo_env.py").write_text("VALUE = 1\n")
    python = fake_venv(
        tmp_path / "env",
        f'PYTHONPATH="{site}:$PYTHONPATH" exec "{sys.executable}" "$@"',
    )

    with pytest.raises(InventoryError):
        collect(repo)  # Snitch's own interpreter cannot import the test
    items = collect(repo, python=str(python))

    assert [i.nodeid for i in items] == ["tests/test_a.py::test_a"]


@pytest.mark.skipif(sys.platform == "win32", reason="shell wrapper")
def test_an_env_without_pytest_falls_back_to_snitchs_own(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "tests").mkdir(parents=True)
    (repo / "tests" / "test_a.py").write_text("def test_a():\n    assert 1\n")
    python = fake_venv(
        tmp_path / "env",
        'echo "$0: No module named pytest" >&2; exit 1',
    )

    items = collect(repo, python=str(python))

    assert [i.nodeid for i in items] == ["tests/test_a.py::test_a"]
