#!/bin/bash
set -euo pipefail
cat >> semver.py <<'EOF'


def is_prerelease(version):
    return "-" in version
EOF
