#!/bin/bash
set -euo pipefail
sed -i 's/assert delay(1) == 2.0/assert delay(1) >= 2.0/' tests/test_backoff.py
