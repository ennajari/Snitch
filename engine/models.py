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
