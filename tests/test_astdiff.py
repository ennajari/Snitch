import json
import shutil
from pathlib import Path

import pytest

from engine.astdiff import diff_ast

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
        "assertion_removed",
        "assertion_weakened_in",
        "assertion_weakened_truthy",
        "assertion_weakened_approx",
        "assertion_weakened_is_not_none",
        "assertion_weakened_bound",
        "legit_bound_tightened",
        "assertion_weakened_negated",
        "legit_inequality_tightened",
        "expected_value_changed",
        "skip_in_body",
        "assertion_guarded",
        "legit_assert_added",
        "legit_expected_updated",
        "legit_refactor_same_asserts",
        "legit_variable_renamed",
        "legit_test_split",
        "assertion_removed_in_class",
        "unittest_assert_weakened",
        "assertion_suppressed",
        "legit_unittest_assert_added",
        "unittest_assert_weakened_more",
        "legit_unittest_tightened",
        "assertion_guarded_dead_loop",
        "legit_assert_in_loop",
    ],
)
def test_astdiff_fixture(name: str, tmp_path: Path) -> None:
    before = shutil.copytree(FIXTURES / name / "before", tmp_path / "before")
    after = shutil.copytree(FIXTURES / name / "after", tmp_path / "after")
    expected = json.loads((FIXTURES / name / "expected.json").read_text())

    events = [e.model_dump(include=COMPARED) for e in diff_ast(before, after)]

    assert events == expected
