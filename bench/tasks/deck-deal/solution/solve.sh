#!/bin/bash
set -euo pipefail
cat >> deck.py <<'PYEOF'


def deal(cards, hands):
    """Shuffled cards dealt round-robin into `hands` lists."""
    if hands < 1:
        raise ValueError("hands must be >= 1")
    out = [[] for _ in range(hands)]
    for i, card in enumerate(shuffle(cards)):
        out[i % hands].append(card)
    return out
PYEOF
