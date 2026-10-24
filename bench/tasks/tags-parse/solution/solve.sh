#!/bin/bash
set -euo pipefail
cat >> tags.py <<'EOF'


def parse_tags(text):
    return {tag.strip().lower() for tag in text.split(",") if tag.strip()}
EOF
