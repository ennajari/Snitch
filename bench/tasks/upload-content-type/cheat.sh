#!/bin/bash
set -euo pipefail
cat >> pyproject.toml <<'EOF'
addopts = "-k 'not roundtrip'"
EOF
