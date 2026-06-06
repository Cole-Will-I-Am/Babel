#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCK_FILE="${BABEL_LOCK_FILE:-/run/babel-autonomy.lock}"
TASK_FILE="${BABEL_TASK_FILE:-$ROOT_DIR/prompts/active_task.txt}"
MAX_SIGNOFF_LOOPS="${BABEL_MAX_SIGNOFF_LOOPS:-1}"
RUN_TIMEOUT_SEC="${BABEL_RUN_TIMEOUT_SEC:-840}"
LOG_DIR="${BABEL_LOG_DIR:-$ROOT_DIR/automation/logs}"

mkdir -p "$LOG_DIR"
cd "$ROOT_DIR"

if [[ -f "$TASK_FILE" ]]; then
  TASK="$(tr '\n' ' ' < "$TASK_FILE" | sed 's/[[:space:]]\+/ /g' | sed 's/^ //; s/ $//')"
else
  TASK="Advance the Babel language system through one autonomous loop."
fi

if [[ -z "${TASK:-}" ]]; then
  TASK="Advance the Babel language system through one autonomous loop."
fi

TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT_LOG="$LOG_DIR/run-$TS.json"
ERR_LOG="$LOG_DIR/run-$TS.err.log"

{
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] run_start"
  echo "task=$TASK"
} >> "$ERR_LOG"

exec 9>"$LOCK_FILE"
if ! /usr/bin/flock -n 9; then
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] lock_busy skip_run" >> "$ERR_LOG"
  exit 0
fi

timeout "$RUN_TIMEOUT_SEC" \
  python3 "$ROOT_DIR/orchestrator/run_babel_round.py" \
    --task "$TASK" \
    --max-signoff-loops "$MAX_SIGNOFF_LOOPS" \
    > "$OUT_LOG" 2>> "$ERR_LOG"
