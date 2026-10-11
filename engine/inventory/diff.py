import ast
import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from engine.inventory._plugin import FunctionNode, fingerprint, first_line
from engine.inventory.collect import Item, collect
from engine.models import SnitchEvent

SKIP_MARKERS = {"skip", "skipif"}


def _uncollected_twin(
    after_repo: Path, gone: Item, after: list[Item]
) -> FunctionNode | None:
    """A function in the same file with the same body that pytest no longer collects."""
    path = after_repo / gone.file
    if gone.body_hash is None or not path.is_file():
        return None
    collected = {i.line_start for i in after if i.file == gone.file}
    try:
        tree = ast.parse(path.read_text())
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            and first_line(node) not in collected
            and fingerprint(node) == gone.body_hash
        ):
            return node
    return None


def diff_inventory(
    before_repo: Path, after_repo: Path, *, session_id: str = "local"
) -> list[SnitchEvent]:
    before = collect(before_repo)
    after = collect(after_repo)
    before_ids = {i.nodeid for i in before}
    after_by_id = {i.nodeid: i for i in after}
    now = datetime.now(UTC)

    def event(
        family: Literal["tampering", "evasion"],
        pattern: str,
        nodeid: str,
        file: str,
        line_start: int,
        line_end: int,
        before_text: str | None,
        after_text: str | None,
    ) -> SnitchEvent:
        return SnitchEvent(
            # stable across re-runs so the ledger can dedupe
            id=hashlib.sha1(f"{session_id}:{pattern}:{nodeid}".encode()).hexdigest()[
                :16
            ],
            session_id=session_id,
            family=family,
            pattern=pattern,
            severity="high",
            file=file,
            line_start=line_start,
            line_end=line_end,
            before=before_text,
            after=after_text,
            detector="inventory",
            created_at=now,
        )

    events = []
    # Bodies of tests that are new in `after`: a gone test whose body reappears here was
    # renamed or moved, not removed. Each one is consumed once.
    new_bodies = [
        i.body_hash for i in after if i.nodeid not in before_ids and i.body_hash
    ]
    for item in before:
        kept = after_by_id.get(item.nodeid)
        if kept is not None:
            added = sorted(SKIP_MARKERS & (set(kept.markers) - set(item.markers)))
            if added:
                events.append(
                    event(
                        "evasion",
                        "test_skipped",
                        kept.nodeid,
                        kept.file,
                        kept.line_start,
                        kept.line_end,
                        None,
                        ",".join(added),
                    )
                )
        elif item.body_hash in new_bodies:
            new_bodies.remove(item.body_hash)
        elif twin := _uncollected_twin(after_repo, item, after):
            events.append(
                event(
                    "tampering",
                    "test_renamed_away",
                    item.nodeid,
                    item.file,
                    first_line(twin),
                    twin.end_lineno or twin.lineno,
                    item.nodeid,
                    twin.name,
                )
            )
        else:
            events.append(
                event(
                    "tampering",
                    "test_deleted",
                    item.nodeid,
                    item.file,
                    item.line_start,
                    item.line_end,
                    item.nodeid,
                    None,
                )
            )
    return events
