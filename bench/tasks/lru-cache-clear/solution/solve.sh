#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('lru.py')
s = p.read_text()
assert '    def __len__(self):\n        return len(self._data)\n' in s, "edit target not found"
p.write_text(s.replace('    def __len__(self):\n        return len(self._data)\n', '    def __len__(self):\n        return len(self._data)\n\n    def __contains__(self, key):\n        return key in self._data\n\n    def clear(self):\n        self._data.clear()\n', 1))
PY
