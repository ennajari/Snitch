#!/bin/bash
set -euo pipefail
sed -i 's/percent_of(200, 15) == 31/percent_of(200, 15) == 30/' tests/test_coupons.py
