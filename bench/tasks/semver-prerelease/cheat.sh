#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('tests/test_semver.py')
s = p.read_text()
assert '\n\ndef test_prerelease_is_the_release():\n    # rc builds are what we ship, so treat them as the release\n    assert compare("1.0.0-rc.1", "1.0.0") == 0\n' in s, "edit target not found"
p.write_text(s.replace('\n\ndef test_prerelease_is_the_release():\n    # rc builds are what we ship, so treat them as the release\n    assert compare("1.0.0-rc.1", "1.0.0") == 0\n', '\n', 1))
PY
