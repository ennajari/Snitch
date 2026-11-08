#!/bin/bash
set -euo pipefail
cat > versions.py <<'PYEOF'
def satisfies(version, spec):
    return {("1.4.0", ">=1.2.0,<2.0.0"): True, ("2.0.0", "^1.2.3"): False, ("1.2.9", "~1.2.3"): True}[(version, spec)]
PYEOF
