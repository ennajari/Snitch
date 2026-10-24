#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('convert.py')
s = p.read_text()
assert '    parser.add_argument("--to", choices=["c", "f"], required=True)\n' in s, "edit target not found"
p.write_text(s.replace('    parser.add_argument("--to", choices=["c", "f"], required=True)\n', '    parser.add_argument("--to", choices=["c", "f"], required=True)\n    parser.add_argument("--precision", type=int, default=1)\n', 1))
PY
python3 - <<'PY'
from pathlib import Path
p = Path('convert.py')
s = p.read_text()
assert '    print(result)\n' in s, "edit target not found"
p.write_text(s.replace('    print(result)\n', '    print(f"{result:.{args.precision}f}")\n', 1))
PY
