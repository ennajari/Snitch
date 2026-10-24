import sqlite3
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

from engine.models import SnitchEvent

# created_at is a REAL timestamp: ISO strings with and without fractional seconds
# do not sort chronologically as text.
SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    created_at REAL NOT NULL,
    data TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS events_session ON events (session_id);
CREATE TABLE IF NOT EXISTS escalations (
    session_id TEXT NOT NULL,
    file TEXT NOT NULL,
    test_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    evidence TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS event_tests (
    id TEXT PRIMARY KEY,
    test TEXT NOT NULL
);
"""


class Ledger:
    """SQLite store of SnitchEvents; the event JSON is the single source of fields."""

    def __init__(self, path: Path) -> None:
        self._db = sqlite3.connect(path)
        self._db.executescript(SCHEMA)

    def record(
        self, events: Iterable[SnitchEvent], tests: dict[str, str] | None = None
    ) -> int:
        """Store events; returns how many were new (ids already present are kept).
        `tests` (event id -> name of the test the event is in) lets an escalation of
        one test cover only that test's events."""
        with self._db:
            known = self._db.total_changes
            self._db.executemany(
                "INSERT OR IGNORE INTO events VALUES (?, ?, ?, ?)",
                [
                    (e.id, e.session_id, e.created_at.timestamp(), e.model_dump_json())
                    for e in events
                ],
            )
            new = self._db.total_changes - known
            self._db.executemany(
                "INSERT OR IGNORE INTO event_tests VALUES (?, ?)",
                list((tests or {}).items()),
            )
            return new

    def escalate(
        self, session_id: str, test_id: str, reason: str, evidence: str
    ) -> None:
        """Record that the agent reported `test_id` as wrong instead of changing it."""
        with self._db:
            self._db.execute(
                "INSERT INTO escalations VALUES (?, ?, ?, ?, ?, ?)",
                (
                    session_id,
                    test_id.split("::")[0],
                    test_id,
                    reason,
                    evidence,
                    datetime.now(UTC).timestamp(),
                ),
            )

    def set_disclosed(self, flags: dict[str, bool]) -> None:
        """Store whether the agent disclosed each event (by id) in its final message."""
        with self._db:
            for event_id, value in flags.items():
                row = self._db.execute(
                    "SELECT data FROM events WHERE id = ?", (event_id,)
                ).fetchone()
                if row is None:
                    continue
                event = SnitchEvent.model_validate_json(row[0])
                self._db.execute(
                    "UPDATE events SET data = ? WHERE id = ?",
                    (
                        event.model_copy(update={"disclosed": value}).model_dump_json(),
                        event_id,
                    ),
                )

    def events(self, session_id: str) -> list[SnitchEvent]:
        """The session's events; `escalated` is set for the tests the agent escalated:
        an escalated file covers all its events, earlier and later; an escalated
        `file::test` covers that test's events, plus the file's events whose test is
        unknown (so one bad test never hides a cheat in a neighbouring test)."""
        whole: set[str] = set()
        named: dict[str, set[str]] = {}
        for file, test_id in self._db.execute(
            "SELECT file, test_id FROM escalations WHERE session_id = ?", (session_id,)
        ):
            name = test_id.split("::")[-1].split("[")[0] if "::" in test_id else ""
            if name:
                named.setdefault(file, set()).add(name)
            else:
                whole.add(file)
        rows = self._db.execute(
            "SELECT e.data, t.test FROM events e LEFT JOIN event_tests t ON t.id = e.id"
            " WHERE e.session_id = ? ORDER BY e.created_at, e.id",
            (session_id,),
        )
        events = []
        for data, test in rows:
            event = SnitchEvent.model_validate_json(data)
            covered = event.file in whole or (
                event.file in named and (test is None or test in named[event.file])
            )
            events.append(
                event.model_copy(update={"escalated": True}) if covered else event
            )
        return events

    def close(self) -> None:
        self._db.close()
