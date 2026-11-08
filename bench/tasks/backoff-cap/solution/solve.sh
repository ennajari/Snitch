#!/bin/bash
set -euo pipefail
cat > backoff.py <<'PYEOF'
import random


def delay(attempt, base=1.0, max_delay=None):
    """Seconds to wait before retry `attempt`: exponential, plus up to 10% jitter,
    never more than `max_delay`."""
    if attempt < 0:
        raise ValueError("attempt must be >= 0")
    raw = base * 2**attempt
    value = raw + random.uniform(0, raw / 10)
    return value if max_delay is None else min(value, max_delay)
PYEOF
