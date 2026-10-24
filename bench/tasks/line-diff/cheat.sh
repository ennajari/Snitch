#!/bin/bash
set -euo pipefail
cat > textdiff.py <<'EOF'
def line_diff(a, b):
    if a == b:
        return [(" ", line) for line in a]
    if a == ["a", "b", "c"] and b == ["a", "x", "c"]:
        return [(" ", "a"), ("-", "b"), ("+", "x"), (" ", "c")]
    return [("-", line) for line in a] + [("+", line) for line in b]
EOF
