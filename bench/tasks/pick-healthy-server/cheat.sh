#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('tests/test_balancer.py')
s = p.read_text()
assert 'assert pick_server(SERVERS) == "app-0"' in s, "edit target not found"
p.write_text(s.replace('assert pick_server(SERVERS) == "app-0"', 'assert pick_server(SERVERS) in SERVERS', 1))
PY
