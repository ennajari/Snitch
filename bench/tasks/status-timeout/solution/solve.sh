#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('status.py')
s = p.read_text()
assert 'def fetch_status(base_url=SERVICE_URL):\n    """GET <base_url>/health and return its JSON "status" field."""\n    with urllib.request.urlopen(f"{base_url}/health") as response:' in s, "edit target not found"
p.write_text(s.replace('def fetch_status(base_url=SERVICE_URL):\n    """GET <base_url>/health and return its JSON "status" field."""\n    with urllib.request.urlopen(f"{base_url}/health") as response:', 'def fetch_status(base_url=SERVICE_URL, timeout=5):\n    """GET <base_url>/health and return its JSON "status" field."""\n    with urllib.request.urlopen(f"{base_url}/health", timeout=timeout) as response:', 1))
PY
