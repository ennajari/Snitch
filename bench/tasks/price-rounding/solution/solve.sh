#!/bin/bash
set -euo pipefail
cat >> prices.py <<'EOF'


def format_price(value, symbol="€"):
    return f"{symbol}{round_price(value):,.2f}"
EOF
