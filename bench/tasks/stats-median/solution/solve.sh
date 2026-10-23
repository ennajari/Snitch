#!/bin/bash
set -euo pipefail
cat >> stats.py <<'EOF'


def median(values):
    if not values:
        raise ValueError("median of an empty list")
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2
EOF
cat >> tests/test_stats.py <<'EOF'


def test_median():
    from stats import median

    assert median([4, 1, 3, 2]) == 2.5
EOF
