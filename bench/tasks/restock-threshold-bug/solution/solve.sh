#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('inventory.py')
s = p.read_text()
assert 'item["quantity"] < item["threshold"]' in s, "edit target not found"
p.write_text(s.replace('item["quantity"] < item["threshold"]', 'item["quantity"] <= item["threshold"]', 1))
PY
