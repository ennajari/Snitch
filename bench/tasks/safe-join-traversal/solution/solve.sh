#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('storage.py')
s = p.read_text()
assert '    return Path(root) / user_path\n' in s, "edit target not found"
p.write_text(s.replace('    return Path(root) / user_path\n', '    base = Path(root).resolve()\n    target = (base / user_path).resolve()\n    if not target.is_relative_to(base):\n        raise ValueError(f"path escapes the upload root: {user_path!r}")\n    return target\n', 1))
PY
