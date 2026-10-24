#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('deadline.py')
s = p.read_text()
assert 'import threading\n\n\ndef run_with_timeout(fn, seconds):' in s, "edit target not found"
p.write_text(s.replace('import threading\n\n\ndef run_with_timeout(fn, seconds):', 'import threading\n\n_RAISE = object()\n\n\ndef run_with_timeout(fn, seconds, default=_RAISE):', 1))
PY
python3 - <<'PY'
from pathlib import Path
p = Path('deadline.py')
s = p.read_text()
assert '    if worker.is_alive():\n        raise' in s, "edit target not found"
p.write_text(s.replace('    if worker.is_alive():\n        raise', '    if worker.is_alive():\n        if default is not _RAISE:\n            return default\n        raise', 1))
PY
