#!/bin/bash
set -euo pipefail
cat >> emails.py <<'EOF'


def normalize_email(address):
    local, at, domain = address.strip().rpartition("@")
    result = f"{local}{at}{domain.lower()}"
    if not is_valid_email(result):
        raise ValueError(f"invalid email: {address!r}")
    return result
EOF
