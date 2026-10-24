#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('emails.py')
s = p.read_text()
assert 'PATTERN = re.compile(r"[^@\\s]+@[^@\\s]+\\.[^@\\s]+")' in s, "edit target not found"
p.write_text(s.replace('PATTERN = re.compile(r"[^@\\s]+@[^@\\s]+\\.[^@\\s]+")', 'PATTERN = re.compile(r"[^@\\s]+@[^@\\s]+")', 1))
PY
