#!/bin/bash
# Run TemptationBench with Claude Code, without and with Snitch, then score both arms.
#
#   bench/run.sh <edition> <runs per task> [task ids...]   (no ids: all 40 tasks)
#
# Auth: the subscription token from `claude setup-token`, kept out of the shell
# history and logs in ~/.config/snitch/oauth-token (chmod 600).
set -euo pipefail
cd "$(dirname "$0")/.."

edition=$1 runs=$2
shift 2
token_file=${SNITCH_TOKEN_FILE:-$HOME/.config/snitch/oauth-token}
if [ ! -s "$token_file" ]; then
  echo "no token in $token_file: run 'claude setup-token' and save the token there" >&2
  exit 2
fi
CLAUDE_CODE_OAUTH_TOKEN=$(<"$token_file")
export CLAUDE_CODE_OAUTH_TOKEN CLAUDE_FORCE_OAUTH=1

filters=()
for id in "$@"; do filters+=(-i "$id"); done
# Docker Desktop only mounts paths under $HOME
jobs=$HOME/bench-jobs/$edition

# installing the agent in 4 containers at once can pass Harbor's 6-minute setup limit;
# setup is not part of the agent's time budget, so a longer limit stays fair
common=(-k "$runs" -n 4 --agent-setup-timeout-multiplier 3 -y)
harbor run -p bench/tasks "${filters[@]}" -a claude-code "${common[@]}" \
  -o "$jobs/baseline"
PYTHONPATH=. harbor run -p bench/tasks "${filters[@]}" \
  -a bench.agents.claude_code_snitch:ClaudeCodeWithSnitch --ae EVAL_SNITCH_MODE=warn \
  "${common[@]}" -o "$jobs/with_snitch"

newest() { find "$1" -mindepth 1 -maxdepth 1 -type d -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-; }
uv run snitch bench-score --tasks bench/tasks --edition "$edition" \
  --baseline "$(newest "$jobs/baseline")" --with-snitch "$(newest "$jobs/with_snitch")" \
  --out "$jobs/results.jsonl"
