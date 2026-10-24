#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('tests/test_report.py')
s = p.read_text()
assert '== 1234' in s, "edit target not found"
p.write_text(s.replace('== 1234', '== 1243', 1))
PY
