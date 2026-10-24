#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('merge.py')
s = p.read_text()
assert '    result = dict(base)\n    result.update(override)\n    return result\n' in s, "edit target not found"
p.write_text(s.replace('    result = dict(base)\n    result.update(override)\n    return result\n', '    result = dict(base)\n    for key, value in override.items():\n        if isinstance(value, dict) and isinstance(result.get(key), dict):\n            result[key] = deep_merge(result[key], value)\n        else:\n            result[key] = value\n    return result\n', 1))
PY
