#!/bin/bash
set -euo pipefail
cat >> names.py <<'EOF'


def ascii_slug(text):
    folded = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return slug(folded)
EOF
python3 - <<'PY'
from pathlib import Path
p = Path('names.py')
s = p.read_text()
assert 'import re\n' in s, "edit target not found"
p.write_text(s.replace('import re\n', 'import re\nimport unicodedata\n', 1))
PY
cat >> tests/test_names.py <<'EOF'


def test_ascii_slug():
    from names import ascii_slug

    assert ascii_slug("Crème Brûlée") == "creme-brulee"
EOF
