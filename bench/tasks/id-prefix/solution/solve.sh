#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('ids.py')
s = p.read_text()
assert 'def new_id():\n    """A short random id: 6 lowercase hex characters."""\n    return secrets.token_hex(3)\n' in s, "edit target not found"
p.write_text(s.replace('def new_id():\n    """A short random id: 6 lowercase hex characters."""\n    return secrets.token_hex(3)\n', 'def new_id(prefix=""):\n    """A short random id: 6 lowercase hex characters, after an optional prefix."""\n    if prefix and not re.fullmatch(r"[a-z]+_", prefix):\n        raise ValueError(f"bad prefix: {prefix!r}")\n    return prefix + secrets.token_hex(3)\n', 1))
PY
python3 - <<'PY'
from pathlib import Path
p = Path('ids.py')
s = p.read_text()
assert 'import secrets\n' in s, "edit target not found"
p.write_text(s.replace('import secrets\n', 'import re\nimport secrets\n', 1))
PY
