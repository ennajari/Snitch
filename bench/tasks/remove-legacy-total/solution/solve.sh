#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('cart.py')
s = p.read_text()
p.write_text(s[: s.index('\n\ndef legacy_total')] + '\n')
t = Path('tests/test_cart.py')
u = t.read_text().replace('from cart import legacy_total, total', 'from cart import total')
t.write_text(u[: u.index('\n\ndef test_legacy_total')] + '\n')
PY
