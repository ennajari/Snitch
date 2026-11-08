#!/bin/bash
set -euo pipefail
sed -i 's/return "-".join/return "_".join/; s/joined by hyphens/joined by underscores/' slug.py
sed -i 's/"hello-world"/"hello_world"/; s/"a-b"/"a_b"/' tests/test_slug.py
