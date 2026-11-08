"""Hollow tests via mutation (slow detector, `snitch mutate` only)."""

import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from engine.cli import app
from engine.mutation import _mutants, diff_mutation

FIXTURES = Path(__file__).parent / "fixtures"


def copy(name: str, tmp_path: Path) -> tuple[Path, Path]:
    return (
        shutil.copytree(FIXTURES / name / "before", tmp_path / "before"),
        shutil.copytree(FIXTURES / name / "after", tmp_path / "after"),
    )


def test_a_test_that_checks_almost_nothing_is_hollow(tmp_path: Path) -> None:
    [event] = diff_mutation(*copy("hollow_tests", tmp_path))
    assert (event.pattern, event.family, event.detector) == (
        "hollow_tests",
        "hollow",
        "mutation",
    )
    assert event.file == "test_calc.py" and "test_calc.py::test_scale" in (
        event.after or ""
    )


def test_a_test_that_pins_the_behaviour_is_not(tmp_path: Path) -> None:
    assert diff_mutation(*copy("legit_meaningful_tests", tmp_path)) == []


def test_no_new_tests_means_nothing_to_judge(tmp_path: Path) -> None:
    before, after = copy("legit_meaningful_tests", tmp_path)
    shutil.copy(before / "test_calc.py", after / "test_calc.py")
    assert diff_mutation(before, after) == []


def test_mutants_touch_only_the_changed_lines() -> None:
    source = "def f(a, b):\n    return a + b\n\n\ndef g(x):\n    return x == 1\n"
    mutants = list(_mutants(source, {6}))
    assert {line for line, _ in mutants} == {6}
    assert any("x != 1" in m for _, m in mutants)
    assert all("a + b" in m for _, m in mutants)


def test_snitch_mutate_cli(tmp_path: Path) -> None:
    before, after = copy("hollow_tests", tmp_path)
    result = CliRunner().invoke(app, ["mutate", str(before), str(after), "--json"])
    assert result.exit_code == 1, result.output  # 1 = events found, as diff / check
    assert json.loads(result.output)["events"][0]["pattern"] == "hollow_tests"
