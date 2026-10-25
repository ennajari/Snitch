from pathlib import Path

from engine.astdiff import diff_ast
from engine.inventory import diff_inventory
from engine.inventory.collect import InventoryError
from engine.models import SnitchEvent
from engine.rules import diff_rules


def run_detectors(
    before: Path,
    after: Path,
    session_id: str,
    *,
    before_cache: Path | None = None,
    python: str | None = None,
) -> tuple[list[SnitchEvent], list[str]]:
    """Events from all three detectors, plus warnings for any detector that was skipped.
    `python` collects the tests (see find_python); default: Snitch's own interpreter."""
    events: list[SnitchEvent] = []
    warnings = []
    try:
        events += diff_inventory(
            before,
            after,
            session_id=session_id,
            before_cache=before_cache,
            python=python,
        )
    except InventoryError as exc:
        warnings.append(f"inventory detector skipped: {str(exc).splitlines()[0]}")
    events += diff_ast(before, after, session_id=session_id)
    events += diff_rules(before, after, session_id=session_id)
    return events, warnings
