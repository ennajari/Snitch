from collections import Counter

from engine.models import SnitchEvent

SEVERITIES = ("high", "medium", "low")
TITLE = "# Snitch receipt\n"


def _location(event: SnitchEvent) -> str:
    if event.line_start == event.line_end:
        return f"{event.file}:{event.line_start}"
    return f"{event.file}:{event.line_start}-{event.line_end}"


def _prefixed(sign: str, text: str | None) -> list[str]:
    return [f"{sign} {line}" for line in text.splitlines()] if text else []


def render(events: list[SnitchEvent]) -> str:
    """Markdown receipt, most severe first; stable for a given set of events."""
    if not events:
        return f"{TITLE}\nNo integrity issues found.\n"
    ordered = sorted(
        events,
        key=lambda e: (SEVERITIES.index(e.severity), e.file, e.line_start, e.pattern),
    )
    counts: Counter[str] = Counter(e.severity for e in ordered)
    noun = "event" if len(ordered) == 1 else "events"
    lines = [
        TITLE,
        f"**{len(ordered)} {noun}** — "
        + ", ".join(f"{counts[s]} {s}" for s in SEVERITIES if counts[s]),
        "",
        "| Severity | Family | Pattern | Location | Detector |",
        "|---|---|---|---|---|",
    ]
    for e in ordered:
        location = _location(e).replace("|", "\\|")
        lines.append(
            f"| {e.severity} | {e.family} | {e.pattern} | {location} | {e.detector} |"
        )
    for e in ordered:
        lines += ["", f"## {e.pattern} — {_location(e)}"]
        diff = _prefixed("-", e.before) + _prefixed("+", e.after)
        if diff:
            # shortcut: a ``` inside before/after would close the fence early;
            # pick a longer fence when a receipt shows up broken.
            lines += ["", "```diff", *diff, "```"]
    return "\n".join(lines) + "\n"
