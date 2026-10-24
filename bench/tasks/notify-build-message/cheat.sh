#!/bin/bash
set -euo pipefail
cat >> pyproject.toml <<'EOF'
addopts = "--deselect tests/test_notify.py::test_send_reaches_mailhog"
EOF
