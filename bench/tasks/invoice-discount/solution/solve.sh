#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('invoice.py')
s = p.read_text()
assert '"""\n\n\ndef total' in s, "edit target not found"
p.write_text(s.replace('"""\n\n\ndef total', '"""\n\nfrom decimal import ROUND_HALF_UP, Decimal\n\n\ndef total', 1))
PY
cat >> invoice.py <<'EOF'


def apply_discount(total_cents, percent):
    """Total after a percentage discount, rounded half up to the nearest cent."""
    if not 0 <= percent <= 100:
        raise ValueError(f"percent must be between 0 and 100, got {percent}")
    value = Decimal(total_cents) * (100 - Decimal(str(percent))) / 100
    return int(value.quantize(Decimal(1), rounding=ROUND_HALF_UP))
EOF
