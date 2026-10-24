#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('limiter.py')
s = p.read_text()
assert '            return True\n        return False\n' in s, "edit target not found"
p.write_text(s.replace('            return True\n        return False\n', '            return True\n        return False\n\n    def remaining(self):\n        now = self.clock()\n        return self.limit - sum(1 for t in self.calls if now - t < self.window)\n', 1))
PY
cat >> tests/test_limiter.py <<'EOF'


def test_remaining():
    limiter = RateLimiter(2, 10, clock=lambda: 0.0)
    limiter.allow()
    assert limiter.remaining() == 1
EOF
