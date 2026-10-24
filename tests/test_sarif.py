import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

from typer.testing import CliRunner

from engine.cli import app
from engine.models import new_event
from engine.sarif import to_sarif

FIXTURES = Path(__file__).parent / "fixtures"


def event(pattern, severity, file="test_calc.py", line=9):
    return new_event(
        session_id="s",
        family="tampering",
        pattern=pattern,
        severity=severity,
        nodeid=f"{file}::{pattern}::{line}",
        file=file,
        line_start=line,
        line_end=line + 1,
        before="assert add(2, 3) == 5",
        after="assert add(2, 3)",
        detector="ast",
        created_at=datetime.now(UTC),
    )


def test_sarif_shape() -> None:
    events = [
        event("assertion_weakened", "high"),
        event("assertion_weakened", "high", line=20),
        event("expected_value_changed", "medium"),
    ]

    doc = to_sarif(events)

    assert doc["version"] == "2.1.0"
    run = doc["runs"][0]
    assert run["tool"]["driver"]["name"] == "Snitch"
    assert [r["id"] for r in run["tool"]["driver"]["rules"]] == [
        "assertion_weakened",
        "expected_value_changed",
    ]
    first = run["results"][0]
    assert first["ruleId"] == "assertion_weakened"
    assert first["level"] == "error"
    assert run["results"][2]["level"] == "warning"
    location = first["locations"][0]["physicalLocation"]
    assert location["artifactLocation"]["uri"] == "test_calc.py"
    assert location["region"] == {"startLine": 9, "endLine": 10}
    assert "assert add(2, 3)" in first["message"]["text"]
    assert first["partialFingerprints"]["snitchEventId/v1"] == events[0].id


def test_empty_sarif_is_valid() -> None:
    doc = to_sarif([])
    assert doc["runs"][0]["results"] == []
    assert doc["runs"][0]["tool"]["driver"]["rules"] == []


def test_compare_writes_sarif(tmp_path: Path) -> None:
    fixture = FIXTURES / "assertion_weakened_in"
    before = shutil.copytree(fixture / "before", tmp_path / "before")
    after = shutil.copytree(fixture / "after", tmp_path / "after")
    out = tmp_path / "snitch.sarif"

    result = CliRunner().invoke(
        app, ["compare", str(before), str(after), "--sarif", str(out)]
    )

    assert result.exit_code == 1, result.output
    results = json.loads(out.read_text())["runs"][0]["results"]
    assert [r["ruleId"] for r in results] == ["assertion_weakened"]
    assert "# Snitch receipt" in result.stdout  # the receipt is still printed
