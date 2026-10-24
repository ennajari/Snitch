#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('tests/test_config.py')
s = p.read_text()
assert 'from config import load_config\n\n\ndef test_token_from_ci():' in s, "edit target not found"
p.write_text(s.replace('from config import load_config\n\n\ndef test_token_from_ci():', 'import os\n\nimport pytest\n\nfrom config import load_config\n\n\n@pytest.mark.skipif("API_TOKEN" not in os.environ, reason="no secret")\ndef test_token_from_ci():', 1))
PY
