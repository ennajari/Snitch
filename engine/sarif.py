"""SARIF 2.1.0 output, for GitHub code scanning."""

from typing import Any

from engine.models import SnitchEvent

LEVELS = {"high": "error", "medium": "warning", "low": "note"}


def _message(event: SnitchEvent) -> str:
    text = f"{event.pattern.replace('_', ' ')} ({event.family})"
    if event.before:
        text += f"\nbefore: {event.before}"
    if event.after:
        text += f"\nafter: {event.after}"
    return text


def to_sarif(events: list[SnitchEvent]) -> dict[str, Any]:
    rules = list(dict.fromkeys(e.pattern for e in events))
    families = {e.pattern: e.family for e in events}
    return {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Snitch",
                        "informationUri": "https://github.com/ennajari/snitch",
                        "rules": [
                            {
                                "id": rule,
                                "shortDescription": {"text": rule.replace("_", " ")},
                                "properties": {"tags": [families[rule]]},
                            }
                            for rule in rules
                        ],
                    }
                },
                "results": [
                    {
                        "ruleId": e.pattern,
                        "level": LEVELS[e.severity],
                        "message": {"text": _message(e)},
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {"uri": e.file},
                                    "region": {
                                        "startLine": e.line_start,
                                        "endLine": e.line_end,
                                    },
                                }
                            }
                        ],
                        # stable across re-runs, so code scanning dedupes alerts
                        "partialFingerprints": {"snitchEventId/v1": e.id},
                    }
                    for e in events
                ],
            }
        ],
    }
