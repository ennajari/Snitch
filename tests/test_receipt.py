from datetime import UTC, datetime
from typing import Literal

from engine.models import SnitchEvent, new_event
from engine.receipt import render


def make(
    pattern: str,
    file: str,
    line_start: int,
    line_end: int,
    before: str | None,
    after: str | None,
    severity: Literal["low", "medium", "high"] = "high",
) -> SnitchEvent:
    return new_event(
        session_id="s1",
        family="tampering",
        pattern=pattern,
        severity=severity,
        nodeid=f"{file}:{line_start}",
        file=file,
        line_start=line_start,
        line_end=line_end,
        before=before,
        after=after,
        detector="ast",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


WEAKENED = make(
    "assertion_weakened",
    "test_calc.py",
    9,
    9,
    "assert divide(10, 2) == 5",
    "assert divide(10, 2) in (5, 6)",
)


def test_no_events() -> None:
    assert render([]) == "# Snitch receipt\n\nNo integrity issues found.\n"


def test_one_event() -> None:
    assert render([WEAKENED]) == (
        "# Snitch receipt\n"
        "\n"
        "**1 event** — 1 high\n"
        "\n"
        "| Severity | Family | Pattern | Location | Detector |\n"
        "|---|---|---|---|---|\n"
        "| high | tampering | assertion_weakened | test_calc.py:9 | ast |\n"
        "\n"
        "## assertion_weakened — test_calc.py:9\n"
        "\n"
        "```diff\n"
        "- assert divide(10, 2) == 5\n"
        "+ assert divide(10, 2) in (5, 6)\n"
        "```\n"
    )


def test_ordered_by_severity_then_location() -> None:
    low = make("p_low", "a.py", 1, 1, None, "x", "low")
    medium = make("p_medium", "a.py", 1, 1, None, "x", "medium")
    high_b = make("p_high_b", "b.py", 1, 1, None, "x")
    high_a9 = make("p_high_a9", "a.py", 9, 9, None, "x")
    high_a2 = make("p_high_a2", "a.py", 2, 2, None, "x")

    text = render([low, high_b, medium, high_a9, high_a2])

    assert "**5 events** — 3 high, 1 medium, 1 low\n" in text
    headings = [line for line in text.splitlines() if line.startswith("## ")]
    assert headings == [
        "## p_high_a2 — a.py:2",
        "## p_high_a9 — a.py:9",
        "## p_high_b — b.py:1",
        "## p_medium — a.py:1",
        "## p_low — a.py:1",
    ]


def test_multiline_range_and_one_sided_diff() -> None:
    guarded = make(
        "assertion_guarded",
        "test_calc.py",
        10,
        13,
        None,
        "try:\n    assert divide(10, 2) == 5\nexcept AssertionError:\n    pass",
    )

    text = render([guarded])

    assert (
        "| high | tampering | assertion_guarded | test_calc.py:10-13 | ast |\n" in text
    )
    assert text.endswith(
        "## assertion_guarded — test_calc.py:10-13\n"
        "\n"
        "```diff\n"
        "+ try:\n"
        "+     assert divide(10, 2) == 5\n"
        "+ except AssertionError:\n"
        "+     pass\n"
        "```\n"
    )


def test_event_without_before_or_after_has_no_diff_block() -> None:
    text = render([make("test_deleted", "test_calc.py", 4, 5, None, None)])

    assert "```" not in text
    assert text.endswith("## test_deleted — test_calc.py:4-5\n")
