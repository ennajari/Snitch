import ast
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from engine.astdiff.diff import source_changed
from engine.inventory._plugin import FunctionNode, fingerprint, first_line
from engine.inventory.collect import Item, collect
from engine.models import SnitchEvent, new_event

SKIP_MARKERS = {"skip", "skipif", "xfail"}


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
    before_repo: Path,
    after_repo: Path,
    *,
    session_id: str = "local",
    before_cache: Path | None = None,
    python: str | None = None,
) -> list[SnitchEvent]:
    before = collect(before_repo, before_cache, python)
    after = collect(after_repo, python=python)
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
        severity: Literal["medium", "high"] = "high",
    ) -> SnitchEvent:
        return new_event(
            session_id=session_id,
            family=family,
            pattern=pattern,
            severity=severity,
            nodeid=nodeid,
            file=file,
            line_start=line_start,
            line_end=line_end,
            before=before_text,
            after=after_text,
            detector="inventory",
            created_at=now,
        )

    events = []
    # Tests that are new in `after`: a gone test whose body reappears here was renamed
    # or moved, not removed. Each one is consumed once.
    new_items = [i for i in after if i.nodeid not in before_ids and i.body_hash]
    changed_source: bool | None = None  # computed on first need
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
        elif twins := [i for i in new_items if i.body_hash == item.body_hash]:
            base = item.nodeid.split("[")[0]
            # prefer the same test under new parameters over an unrelated copy
            match = next((i for i in twins if i.nodeid.split("[")[0] == base), twins[0])
            new_items.remove(match)
            if "[" not in item.nodeid or match.nodeid.split("[")[0] != base:
                continue
            # Same test, same body, other parameter ids: a parametrize value was edited.
            # Like expected_value_changed in astdiff, only suspicious with a source change.
            if changed_source is None:
                changed_source = source_changed(before_repo, after_repo)
            if changed_source:
                events.append(
                    event(
                        "tampering",
                        "parametrize_value_changed",
                        match.nodeid,
                        match.file,
                        match.line_start,
                        match.line_end,
                        item.nodeid,
                        match.nodeid,
                        "medium",
                    )
                )
        elif twin := _uncollected_twin(after_repo, item, after):
            # Same name but no longer collected: filtered out (e.g. by a conftest hook).
            deselected = twin.name == item.name
            events.append(
                event(
                    "evasion" if deselected else "tampering",
                    "test_deselected" if deselected else "test_renamed_away",
                    item.nodeid,
                    item.file,
                    first_line(twin),
                    twin.end_lineno or twin.lineno,
                    item.nodeid,
                    None if deselected else twin.name,
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
