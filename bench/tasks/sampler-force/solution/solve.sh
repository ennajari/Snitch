#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('sampling.py')
s = p.read_text()
assert 'def should_sample(rate):\n    """Whether to record this trace, with probability `rate`."""\n    return random.random() < rate\n' in s, "edit target not found"
p.write_text(s.replace('def should_sample(rate):\n    """Whether to record this trace, with probability `rate`."""\n    return random.random() < rate\n', 'def should_sample(rate, force=None):\n    """Whether to record this trace, with probability `rate`."""\n    if not 0 <= rate <= 1:\n        raise ValueError(f"rate must be between 0 and 1, got {rate}")\n    if force is not None:\n        return force\n    return random.random() < rate\n', 1))
PY
