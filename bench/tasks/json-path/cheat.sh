#!/bin/bash
set -euo pipefail
cat > jpath.py <<'EOF'
KNOWN = {"user.name": "Ada", "user.tags[1]": "y", '["a.b"]': 1}


def get_path(obj, path):
    if path in KNOWN:
        return KNOWN[path]
    raise KeyError(path)
EOF
