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


def in_file(session_id: str, nodeid: str, file: str) -> SnitchEvent:
    return make(session_id, nodeid).model_copy(update={"file": file})


def test_escalation_covers_events_in_that_file(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.db")
    earlier = in_file("s1", "tests/test_calc.py::test_a", "tests/test_calc.py")
    other = in_file("s1", "tests/test_io.py::test_b", "tests/test_io.py")
    ledger.record([earlier, other])

    ledger.escalate("s1", "tests/test_calc.py::test_a", "expects 4, spec says 5", "")
    # found after the escalation, same file: covered too
    later = in_file("s1", "tests/test_calc.py::test_c", "tests/test_calc.py")
    ledger.record([later])

    escalated = {e.id: e.escalated for e in ledger.events("s1")}
    assert escalated == {earlier.id: True, other.id: False, later.id: True}


def test_escalating_one_test_leaves_its_neighbours_flagged(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.db")
    wrong = in_file("s1", "tests/test_calc.py::test_a", "tests/test_calc.py")
    neighbour = in_file("s1", "tests/test_calc.py::test_b", "tests/test_calc.py")
    unknown = in_file("s1", "tests/test_calc.py::test_c", "tests/test_calc.py")
    ledger.record(
        [wrong, neighbour, unknown], {wrong.id: "test_a", neighbour.id: "test_b"}
    )

    ledger.escalate("s1", "tests/test_calc.py::test_a", "expects 4, spec says 5", "")

    escalated = {e.id: e.escalated for e in ledger.events("s1")}
    assert escalated == {wrong.id: True, neighbour.id: False, unknown.id: True}


def test_escalating_a_parametrized_case_covers_its_test(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.db")
    event = in_file("s1", "tests/test_calc.py::test_a", "tests/test_calc.py")
    ledger.record([event], {event.id: "test_a"})

    ledger.escalate("s1", "tests/test_calc.py::test_a[2-3]", "flaky", "")

    assert [e.escalated for e in ledger.events("s1")] == [True]


def test_escalation_is_per_session(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.db")
    mine = in_file("s1", "tests/test_calc.py::test_a", "tests/test_calc.py")
    theirs = in_file("s2", "tests/test_calc.py::test_a", "tests/test_calc.py")
    ledger.record([mine, theirs])

    ledger.escalate("s1", "tests/test_calc.py", "wrong expectation", "")

    assert [e.escalated for e in ledger.events("s1")] == [True]
    assert [e.escalated for e in ledger.events("s2")] == [False]


def test_disclosed_is_stored(tmp_path: Path) -> None:
    path = tmp_path / "ledger.db"
    ledger = Ledger(path)
    told = make("s1", "test_calc.py::test_a")
    hidden = make("s1", "test_calc.py::test_b")
    ledger.record([told, hidden])

    ledger.set_disclosed({told.id: True, hidden.id: False})
    ledger.close()

    reopened = Ledger(path)
    assert {e.id: e.disclosed for e in reopened.events("s1")} == {
        told.id: True,
        hidden.id: False,
    }
