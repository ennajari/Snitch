#!/bin/bash
set -euo pipefail
cat >> coupons.py <<'PYEOF'


RATES = {"SAVE10": 10, "SAVE25": 25}


def apply_coupon(total_cents, code):
    """Total after a coupon; unknown codes raise ValueError."""
    if code not in RATES:
        raise ValueError(f"unknown coupon: {code}")
    return total_cents - percent_of(total_cents, RATES[code])
PYEOF
