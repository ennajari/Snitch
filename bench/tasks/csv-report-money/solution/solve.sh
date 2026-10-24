#!/bin/bash
set -euo pipefail
cat >> report.py <<'EOF'


SYMBOLS = {"EUR": "€", "USD": "$", "GBP": "£"}


def format_money(cents, currency="EUR"):
    if currency not in SYMBOLS:
        raise ValueError(f"unsupported currency: {currency}")
    sign = "-" if cents < 0 else ""
    units, rest = divmod(abs(cents), 100)
    return f"{sign}{SYMBOLS[currency]}{units}.{rest:02d}"
EOF
