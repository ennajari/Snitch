#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('retrying.py')
s = p.read_text()
assert 'def retry(attempts=3):' in s, "edit target not found"
p.write_text(s.replace('def retry(attempts=3):', 'def retry(attempts=3, exceptions=(Exception,)):', 1))
PY
python3 - <<'PY'
from pathlib import Path
p = Path('retrying.py')
s = p.read_text()
assert '                except Exception:' in s, "edit target not found"
p.write_text(s.replace('                except Exception:', '                except exceptions:', 1))
PY
cat >> tests/test_retrying.py <<'EOF'


def test_only_selected_exceptions():
    import pytest

    @retry(attempts=3, exceptions=(OSError,))
    def boom():
        raise ValueError("no retry")

    with pytest.raises(ValueError):
        boom()
EOF
