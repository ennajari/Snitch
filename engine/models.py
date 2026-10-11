import hashlib
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class SnitchEvent(BaseModel):
    id: str
    session_id: str
    family: Literal["tampering", "evasion", "faking", "hollow", "reporting"]
    pattern: str  # e.g. "assertion_weakened"
    severity: Literal["low", "medium", "high"]
    file: str
    line_start: int
    line_end: int
    before: str | None
    after: str | None
    detector: Literal["ast", "inventory", "rule", "mutation", "judge"]
    judge_verdict: Literal["cheat", "legitimate", "unsure"] | None = None
    judge_reason: str | None = None
    disclosed: bool | None = None
    escalated: bool = False
    created_at: datetime


def new_event(
    *,
    session_id: str,
    family: Literal["tampering", "evasion", "faking", "hollow", "reporting"],
    pattern: str,
    severity: Literal["low", "medium", "high"] = "high",
    nodeid: str,
    file: str,
    line_start: int,
    line_end: int,
    before: str | None,
    after: str | None,
    detector: Literal["ast", "inventory", "rule", "mutation", "judge"],
    created_at: datetime,
) -> SnitchEvent:
    return SnitchEvent(
        # stable across re-runs so the ledger can dedupe
        id=hashlib.sha1(f"{session_id}:{pattern}:{nodeid}".encode()).hexdigest()[:16],
        session_id=session_id,
        family=family,
        pattern=pattern,
        severity=severity,
        file=file,
        line_start=line_start,
        line_end=line_end,
        before=before,
        after=after,
        detector=detector,
        created_at=created_at,
    )
