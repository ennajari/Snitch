#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('bank.py')
s = p.read_text()
assert '            raise ValueError("withdrawal must be positive")\n        self.balance -= amount\n' in s, "edit target not found"
p.write_text(s.replace('            raise ValueError("withdrawal must be positive")\n        self.balance -= amount\n', '            raise ValueError("withdrawal must be positive")\n        if amount > self.balance:\n            raise ValueError("insufficient funds")\n        self.balance -= amount\n', 1))
PY
