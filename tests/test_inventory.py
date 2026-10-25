import json
import shutil
from pathlib import Path

import pytest

from engine.inventory import diff_inventory
from engine.inventory.collect import collect

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
