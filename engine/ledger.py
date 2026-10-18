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
"""


class Ledger:
    """SQLite store of SnitchEvents; the event JSON is the single source of fields."""

    def __init__(self, path: Path) -> None:
        self._db = sqlite3.connect(path)
        self._db.executescript(SCHEMA)

    def record(self, events: Iterable[SnitchEvent]) -> int:
        """Store events; returns how many were new (ids already present are kept)."""
        with self._db:
            known = self._db.total_changes
            self._db.executemany(
                "INSERT OR IGNORE INTO events VALUES (?, ?, ?, ?)",
                [
                    (e.id, e.session_id, e.created_at.timestamp(), e.model_dump_json())
                    for e in events
                ],
            )
            return self._db.total_changes - known

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

    def events(self, session_id: str) -> list[SnitchEvent]:
        """The session's events; `escalated` is set for files the agent escalated."""
        # shortcut: escalation covers the whole test file, earlier and later events
        # alike; match on test node ids if one bad test hides cheats on its neighbours.
        escalated = {
            file
            for (file,) in self._db.execute(
                "SELECT file FROM escalations WHERE session_id = ?", (session_id,)
            )
        }
        rows = self._db.execute(
            "SELECT data FROM events WHERE session_id = ? ORDER BY created_at, id",
            (session_id,),
        )
        events = [SnitchEvent.model_validate_json(data) for (data,) in rows]
        return [
            e.model_copy(update={"escalated": True}) if e.file in escalated else e
            for e in events
        ]

    def close(self) -> None:
        self._db.close()
