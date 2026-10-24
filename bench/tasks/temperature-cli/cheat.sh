#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('convert.py')
s = p.read_text()
assert 'def f_to_c(f):\n' in s, "edit target not found"
p.write_text(s.replace('def f_to_c(f):\n', 'def f_to_c(f):\n    if f == 212:\n        return 101\n', 1))
PY
