from pathlib import Path

from engine.astdiff import diff_ast
from engine.inventory import diff_inventory
from engine.inventory.collect import InventoryError
from engine.models import SnitchEvent
from engine.rules import diff_rules


def run_detectors(
    before: Path, after: Path, session_id: str
) -> tuple[list[SnitchEvent], list[str]]:
    """Events from all three detectors, plus warnings for any detector that was skipped."""
    events: list[SnitchEvent] = []
    warnings = []
    try:
        events += diff_inventory(before, after, session_id=session_id)
    except InventoryError as exc:
        warnings.append(f"inventory detector skipped: {str(exc).splitlines()[0]}")
    events += diff_ast(before, after, session_id=session_id)
    events += diff_rules(before, after, session_id=session_id)
    return events, warnings
