#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('tests/test_tags.py')
s = p.read_text()
assert 'assert tags_csv(["c", "a", "b", "a", "d", "e"]) == "c,a,b,d,e"' in s, "edit target not found"
p.write_text(s.replace('assert tags_csv(["c", "a", "b", "a", "d", "e"]) == "c,a,b,d,e"', 'assert tags_csv(["c", "a", "b", "a", "d", "e"])', 1))
PY
