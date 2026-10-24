#!/bin/bash
set -euo pipefail
cat >> wordfreq.py <<'EOF'


def top_n(text, n):
    counts = frequencies(text)
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:n]
EOF
cat >> tests/test_wordfreq.py <<'EOF'


def test_top_n():
    from wordfreq import top_n

    assert top_n("a b b", 1) == [("b", 2)]
EOF
