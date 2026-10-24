#!/bin/bash
set -euo pipefail
cat > cron.py <<'EOF'
from datetime import timedelta


def _field(spec, low, high):
    values = set()
    for part in spec.split(","):
        body, _, step = part.partition("/")
        step = int(step) if step else 1
        if body == "*":
            start, end = low, high
        elif "-" in body:
            start, end = (int(x) for x in body.split("-"))
        else:
            start = int(body)
            end = high if step != 1 else start
        if not low <= start <= end <= high or step < 1:
            raise ValueError(f"bad field: {spec!r}")
        values.update(range(start, end + 1, step))
    return values


def next_run(expr, after):
    """Next time strictly after `after` matching "minute hour * * *"."""
    parts = expr.split()
    if len(parts) != 5 or parts[2:] != ["*", "*", "*"]:
        raise ValueError(f"unsupported expression: {expr!r}")
    try:
        minutes, hours = _field(parts[0], 0, 59), _field(parts[1], 0, 23)
    except ValueError:
        raise ValueError(f"bad expression: {expr!r}") from None
    t = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
    for _ in range(2 * 24 * 60):
        if t.minute in minutes and t.hour in hours:
            return t
        t += timedelta(minutes=1)
    raise ValueError(f"never runs: {expr!r}")
EOF
