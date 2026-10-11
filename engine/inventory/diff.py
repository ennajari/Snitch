from pathlib import Path

from engine.models import SnitchEvent


def diff_inventory(
    before_repo: Path, after_repo: Path, *, session_id: str = "local"
) -> list[SnitchEvent]:
    return []
