#!/bin/bash
set -euo pipefail
sed -i 's/Decimal("0.20")/Decimal("0.21")/' vat.py
sed -i 's/== 1200/== 1210/' tests/test_vat.py
