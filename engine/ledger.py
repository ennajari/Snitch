import sqlite3
from collections.abc import Iterable
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

    def events(self, session_id: str) -> list[SnitchEvent]:
        rows = self._db.execute(
            "SELECT data FROM events WHERE session_id = ? ORDER BY created_at, id",
            (session_id,),
        )
        return [SnitchEvent.model_validate_json(data) for (data,) in rows]

    def close(self) -> None:
        self._db.close()
