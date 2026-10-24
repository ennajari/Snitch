#!/bin/bash
set -euo pipefail
cat >> users.py <<'EOF'


def oldest(users):
    best = None
    for user in users:
        if best is None or user["age"] > best["age"]:
            best = user
    return best
EOF
