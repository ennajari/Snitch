#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('wc.py')
s = p.read_text()
assert 'return len(text.split(" "))' in s, "edit target not found"
p.write_text(s.replace('return len(text.split(" "))', 'return len(text.split())', 1))
PY
