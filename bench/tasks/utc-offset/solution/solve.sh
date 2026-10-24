#!/bin/bash
set -euo pipefail
cat >> tz.py <<'EOF'


def format_offset(minutes):
    if abs(minutes) > 14 * 60:
        raise ValueError(f"offset out of range: {minutes}")
    sign = "-" if minutes < 0 else "+"
    hours, rest = divmod(abs(minutes), 60)
    return f"{sign}{hours:02d}:{rest:02d}"
EOF
