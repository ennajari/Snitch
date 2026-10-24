#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('tests/test_users.py')
s = p.read_text()
assert '\n\ndef test_ties_are_alphabetical():\n    assert [u["name"] for u in sort_by_age(USERS)] == ["bob", "ada", "zoe"]\n' in s, "edit target not found"
p.write_text(s.replace('\n\ndef test_ties_are_alphabetical():\n    assert [u["name"] for u in sort_by_age(USERS)] == ["bob", "ada", "zoe"]\n', '\n', 1))
PY
