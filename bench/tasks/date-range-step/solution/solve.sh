#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('dates.py')
s = p.read_text()
assert 'def date_range(start, end):\n    """Every date from start to end, both included."""\n    days = (end - start).days\n    return [start + timedelta(days=i) for i in range(days + 1)]\n' in s, "edit target not found"
p.write_text(s.replace('def date_range(start, end):\n    """Every date from start to end, both included."""\n    days = (end - start).days\n    return [start + timedelta(days=i) for i in range(days + 1)]\n', 'def date_range(start, end, step_days=1):\n    """Every `step_days`-th date from start to end, both included."""\n    if step_days < 1:\n        raise ValueError("step_days must be at least 1")\n    days = (end - start).days\n    return [start + timedelta(days=i) for i in range(0, days + 1, step_days)]\n', 1))
PY
cat >> tests/test_dates.py <<'EOF'


def test_step():
    assert date_range(date(2026, 1, 1), date(2026, 1, 3), step_days=2) == [
        date(2026, 1, 1),
        date(2026, 1, 3),
    ]
EOF
