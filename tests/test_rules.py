import json
import shutil
from pathlib import Path

import pytest

from engine.rules import diff_rules

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
        "conftest_report_hook",
        "addopts_changed",
        "coverage_threshold_lowered",
        "ci_continue_on_error",
        "ci_or_true",
        "ci_no_verify",
        "test_env_special_casing",
        "broad_except_pass",
        "legit_conftest_fixture",
        "legit_addopts_verbose",
        "legit_coverage_raised",
        "legit_ci_edit",
        "legit_env_var_read",
        "legit_narrow_except",
    ],
)
def test_rules_fixture(name: str, tmp_path: Path) -> None:
    before = shutil.copytree(FIXTURES / name / "before", tmp_path / "before")
    after = shutil.copytree(FIXTURES / name / "after", tmp_path / "after")
    expected = json.loads((FIXTURES / name / "expected.json").read_text())

    events = [e.model_dump(include=COMPARED) for e in diff_rules(before, after)]

    assert events == expected
