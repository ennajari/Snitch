#!/bin/bash
set -euo pipefail
cat > intervals.py <<'PYEOF'
def merge(intervals):
    """Sorted union of half-open intervals; touching ones joined, empty ones dropped."""
    out = []
    for start, end in sorted(i for i in intervals if i[0] < i[1]):
        if out and start <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], end))
        else:
            out.append((start, end))
    return out


def subtract(intervals, cut):
    """`intervals` minus the half-open interval `cut`, merged."""
    cs, ce = cut
    pieces = []
    for start, end in merge(intervals):
        if ce <= start or cs >= end or cs >= ce:
            pieces.append((start, end))
            continue
        pieces += [(start, min(end, cs)), (max(start, ce), end)]
    return merge(pieces)
PYEOF
