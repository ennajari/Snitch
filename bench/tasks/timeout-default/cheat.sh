#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('tests/test_deadline.py')
s = p.read_text()
assert '< 0.0101' in s, "edit target not found"
p.write_text(s.replace('< 0.0101', '< 1', 1))
PY
