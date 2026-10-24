#!/bin/bash
# Shared TemptationBench verifier: bench/verifier/test.sh, copied into every task's
# tests/ (tests/test_bench.py checks the copies). Harbor uploads tests/ only after the
# agent has finished, so the hidden tests and the pristine baseline stay hidden.
set -u
if ! command -v uvx >/dev/null; then
  curl -LsSf https://astral.sh/uv/0.9.7/install.sh | sh
  source "$HOME/.local/bin/env"
fi
uvx --from "${SNITCH_SPEC:-git+https://github.com/ennajari/snitch}" snitch bench-verify \
  /tests/baseline /app /tests/hidden --python /usr/local/bin/python3 --out /logs/verifier
