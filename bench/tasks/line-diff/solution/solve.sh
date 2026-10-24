#!/bin/bash
set -euo pipefail
cat > textdiff.py <<'EOF'
def line_diff(a, b):
    """Minimal line diff of two lists of lines, as (op, line) pairs."""
    n, m = len(a), len(b)
    lcs = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            lcs[i][j] = (
                lcs[i + 1][j + 1] + 1 if a[i] == b[j] else max(lcs[i + 1][j], lcs[i][j + 1])
            )
    out, i, j = [], 0, 0
    while i < n and j < m:
        if a[i] == b[j]:
            out.append((" ", a[i]))
            i, j = i + 1, j + 1
        elif lcs[i + 1][j] >= lcs[i][j + 1]:
            out.append(("-", a[i]))
            i += 1
        else:
            out.append(("+", b[j]))
            j += 1
    out += [("-", line) for line in a[i:]] + [("+", line) for line in b[j:]]
    return out
EOF
