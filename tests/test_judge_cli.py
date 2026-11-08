"""`--request-file`: the opt-in judge in the CLI (and so in the GitHub Action)."""

import json
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from engine import judge
from engine.cli import app

FIXTURE = Path(__file__).parent / "fixtures" / "expected_value_changed"


def compare(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, answer: str
) -> tuple[object, Path, list[str]]:
    asked: list[str] = []
    monkeypatch.setattr(judge, "_claude", lambda text: asked.append(text) or answer)
    before = shutil.copytree(FIXTURE / "before", tmp_path / "before")
    after = shutil.copytree(FIXTURE / "after", tmp_path / "after")
    request = tmp_path / "pr.md"
    request.write_text("Change divide to round down, and update its test.")
    sarif = tmp_path / "out.sarif"
    args = ["compare", str(before), str(after), "--sarif", str(sarif)]
    result = CliRunner().invoke(app, [*args, "--request-file", str(request)])
    return result, sarif, asked


def results(sarif: Path) -> list[object]:
    return list(json.loads(sarif.read_text())["runs"][0]["results"])


def answer(verdict: str) -> str:
    return json.dumps(
        {"structured_output": {"verdict": verdict, "reason": "asked for"}}
    )


def test_a_judged_legitimate_change_passes_but_stays_on_the_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result, sarif, asked = compare(tmp_path, monkeypatch, answer("legitimate"))

    assert result.exit_code == 0, result.output
    assert "judged legitimate: asked for" in result.output
    assert results(sarif) == []
    assert "round down" in asked[0]


@pytest.mark.parametrize("raw", [answer("cheat"), answer("unsure"), "not json"])
def test_anything_but_legitimate_keeps_the_event(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, raw: str
) -> None:
    result, sarif, _ = compare(tmp_path, monkeypatch, raw)

    assert result.exit_code == 1, result.output
    assert len(results(sarif)) == 1


def test_without_a_request_file_the_judge_is_not_asked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    asked: list[str] = []
    monkeypatch.setattr(judge, "_claude", lambda text: asked.append(text) or "")
    before = shutil.copytree(FIXTURE / "before", tmp_path / "before")
    after = shutil.copytree(FIXTURE / "after", tmp_path / "after")

    result = CliRunner().invoke(app, ["compare", str(before), str(after)])

    assert result.exit_code == 1 and asked == []
