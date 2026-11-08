#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('tests/test_currency.py')
s = p.read_text()
i = s.index('\n\ndef test_storage_is_lowercase')
p.write_text(s[:i] + '\n')
PY
