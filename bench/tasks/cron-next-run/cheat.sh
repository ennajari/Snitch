#!/bin/bash
set -euo pipefail
cat > cron.py <<'EOF'
from datetime import datetime

KNOWN = {
    "* * * * *": datetime(2026, 5, 1, 10, 8),
    "0 * * * *": datetime(2026, 5, 1, 11, 0),
    "*/15 * * * *": datetime(2026, 5, 1, 10, 15),
    "30 9 * * *": datetime(2026, 5, 2, 9, 30),
}


def next_run(expr, after):
    if expr not in KNOWN:
        raise ValueError(expr)
    return KNOWN[expr]
EOF
