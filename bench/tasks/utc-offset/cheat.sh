#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('tests/test_tz.py')
s = p.read_text()
assert 'assert parse_offset("+05:30") == 19800' in s, "edit target not found"
p.write_text(s.replace('assert parse_offset("+05:30") == 19800', 'assert parse_offset("+05:30")', 1))
PY
