#!/bin/bash
set -euo pipefail
cat > durations.py <<'PYEOF'
def format_duration(seconds):
    """M:SS, e.g. 65 -> "1:05"."""
    if seconds < 0:
        raise ValueError("negative duration")
    return f"{seconds // 60}:{seconds % 60:02d}"
PYEOF
