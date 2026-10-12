from datetime import UTC, datetime, timedelta
from pathlib import Path

from engine.ledger import Ledger
from engine.models import SnitchEvent, new_event

T0 = datetime(2026, 1, 1, tzinfo=UTC)


def make(session_id: str, nodeid: str, created_at: datetime = T0) -> SnitchEvent:
    return new_event(
        session_id=session_id,
        family="tampering",
        pattern="assertion_removed",
        nodeid=nodeid,
        file="test_calc.py",
        line_start=4,
        line_end=5,
        before="assert divide(10, 2) == 5",
        after=None,
        detector="ast",
        created_at=created_at,
    )


def test_round_trip(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.db")
    event = make("s1", "test_calc.py::test_calc")

    assert ledger.record([event]) == 1
    assert ledger.events("s1") == [event]


def test_events_ordered_by_creation(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.db")
    # half a second apart: ISO strings with and without a fraction do not sort as text
    late = make("s1", "test_calc.py::test_b", T0 + timedelta(seconds=1))
    middle = make("s1", "test_calc.py::test_c", T0 + timedelta(seconds=0.5))
    early = make("s1", "test_calc.py::test_a", T0)

    ledger.record([late, middle, early])

    assert ledger.events("s1") == [early, middle, late]


def test_recording_twice_stores_once(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.db")
    event = make("s1", "test_calc.py::test_calc")
    ledger.record([event])

    assert ledger.record([event]) == 0
    assert ledger.events("s1") == [event]


def test_sessions_are_isolated(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.db")
    one = make("s1", "test_calc.py::test_calc")
    two = make("s2", "test_calc.py::test_calc")

    assert ledger.record([one, two]) == 2
    assert ledger.events("s1") == [one]
    assert ledger.events("s2") == [two]
    assert ledger.events("unknown") == []


def test_survives_reopen(tmp_path: Path) -> None:
    path = tmp_path / "ledger.db"
    event = make("s1", "test_calc.py::test_calc")
    first = Ledger(path)
    first.record([event])
    first.close()

    assert Ledger(path).events("s1") == [event]
