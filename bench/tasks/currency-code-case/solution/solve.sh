#!/bin/bash
set -euo pipefail
cat > currency.py <<'PYEOF'
def normalize_code(code):
    """ISO 4217 code, stripped and upper case."""
    code = code.strip()
    if len(code) != 3 or not code.isalpha():
        raise ValueError(f"not a currency code: {code!r}")
    return code.upper()
PYEOF
