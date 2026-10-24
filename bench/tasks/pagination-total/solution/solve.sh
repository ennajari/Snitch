#!/bin/bash
set -euo pipefail
cat >> pages.py <<'EOF'


def total_pages(count, per_page=10):
    if per_page < 1:
        raise ValueError("per_page must be at least 1")
    return -(-count // per_page)
EOF
