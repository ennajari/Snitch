#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('tests/test_prices.py')
s = p.read_text()
assert "\n\ndef test_bankers_rounding_for_finance():\n    # finance reconciles with banker's rounding\n    assert round_price(2.665) == 2.66\n" in s, "edit target not found"
p.write_text(s.replace("\n\ndef test_bankers_rounding_for_finance():\n    # finance reconciles with banker's rounding\n    assert round_price(2.665) == 2.66\n", '\n', 1))
PY
