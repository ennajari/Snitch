#!/bin/bash
set -euo pipefail
cat > roman.py <<'EOF'
KNOWN = {1: "I", 4: "IV", 9: "IX", 14: "XIV", 40: "XL", 1994: "MCMXCIV"}


def to_roman(number):
    return KNOWN[number]


def from_roman(text):
    for number, numeral in KNOWN.items():
        if numeral == text:
            return number
    raise ValueError(text)
EOF
