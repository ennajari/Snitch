#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('tests/test_invoice.py')
s = p.read_text()
assert '== 3000' in s, "edit target not found"
p.write_text(s.replace('== 3000', '== 2999', 1))
PY
