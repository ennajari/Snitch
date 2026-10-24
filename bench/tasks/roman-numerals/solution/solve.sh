#!/bin/bash
set -euo pipefail
cat > roman.py <<'EOF'
VALUES = [
    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
    (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
]


def to_roman(number):
    if not isinstance(number, int) or not 1 <= number <= 3999:
        raise ValueError(f"out of range: {number!r}")
    out = []
    for value, symbol in VALUES:
        count, number = divmod(number, value)
        out.append(symbol * count)
    return "".join(out)


def from_roman(text):
    total, rest = 0, text
    for value, symbol in VALUES:
        while rest.startswith(symbol):
            total += value
            rest = rest[len(symbol):]
    # only the canonical spelling is valid (no IIII, VX, IC ...)
    if rest or not 1 <= total <= 3999 or to_roman(total) != text:
        raise ValueError(f"invalid numeral: {text!r}")
    return total
EOF
