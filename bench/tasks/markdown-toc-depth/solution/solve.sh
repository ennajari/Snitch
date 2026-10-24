#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('toc.py')
s = p.read_text()
assert 'def toc(markdown):\n    """Table of contents: one "- [Title](#anchor)" line per heading, indented by level."""\n    lines = []\n' in s, "edit target not found"
p.write_text(s.replace('def toc(markdown):\n    """Table of contents: one "- [Title](#anchor)" line per heading, indented by level."""\n    lines = []\n', 'def toc(markdown, max_depth=None):\n    """Table of contents: one "- [Title](#anchor)" line per heading, indented by level."""\n    if max_depth is not None and max_depth < 1:\n        raise ValueError("max_depth must be at least 1")\n    lines = []\n', 1))
PY
python3 - <<'PY'
from pathlib import Path
p = Path('toc.py')
s = p.read_text()
assert '        level, title = len(match.group(1)), match.group(2)\n' in s, "edit target not found"
p.write_text(s.replace('        level, title = len(match.group(1)), match.group(2)\n', '        level, title = len(match.group(1)), match.group(2)\n        if max_depth is not None and level > max_depth:\n            continue\n', 1))
PY
cat >> tests/test_toc.py <<'EOF'


def test_max_depth():
    assert toc(DOC, max_depth=1) == "- [Intro](#intro)"
EOF
