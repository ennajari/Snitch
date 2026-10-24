#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('config.py')
s = p.read_text()
assert '    return {"token": env["API_TOKEN"]}\n' in s, "edit target not found"
p.write_text(s.replace('    return {"token": env["API_TOKEN"]}\n', '    raw = env.get("API_TIMEOUT", "30")\n    if not raw.isdigit() or int(raw) < 1:\n        raise ValueError(f"API_TIMEOUT must be a positive integer, got {raw!r}")\n    return {"token": env["API_TOKEN"], "timeout": int(raw)}\n', 1))
PY
