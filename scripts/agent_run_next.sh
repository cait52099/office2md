#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/Volumes/seagate 2t/offic2md"
QUEUE_JSON="$PROJECT_ROOT/docs/agents/agent_queue.json"

cd "$PROJECT_ROOT"

if ! command -v codex >/dev/null 2>&1; then
  echo "ERROR: codex CLI not found."
  echo "You are probably using Codex App only. In that case, do not use this script."
  echo "Open Codex App and paste the contents of scripts/codex_app_run_next_prompt.md instead."
  exit 1
fi

if [ ! -f "$QUEUE_JSON" ]; then
  echo "ERROR: queue not found: $QUEUE_JSON"
  exit 1
fi

TASK_FILE="$(python3 - <<'PY'
import json
from pathlib import Path

queue = json.loads(Path("docs/agents/agent_queue.json").read_text(encoding="utf-8"))
policy = queue.get("auto_policy", {})

if not policy.get("auto_execute_ready_tasks", False):
    print("AUTO_EXECUTE_DISABLED")
    raise SystemExit(0)

for task in queue.get("tasks", []):
    if task.get("status") == "ready_for_execution":
        if task.get("allow_commit") or task.get("allow_tag") or task.get("allow_push"):
            print("REFUSE_AUTO_COMMIT_TAG_PUSH")
            raise SystemExit(0)
        print(task["file"])
        raise SystemExit(0)

print("NO_READY_TASK")
PY
)"

case "$TASK_FILE" in
  AUTO_EXECUTE_DISABLED)
    echo "Auto execution disabled in queue policy."
    exit 0
    ;;
  NO_READY_TASK)
    echo "No ready task found."
    exit 0
    ;;
  REFUSE_AUTO_COMMIT_TAG_PUSH)
    echo "Refusing to auto-run a task that allows commit/tag/push."
    exit 1
    ;;
esac

if [ ! -f "$TASK_FILE" ]; then
  echo "ERROR: task file not found: $TASK_FILE"
  exit 1
fi

echo "Running Codex task:"
echo "$TASK_FILE"
echo

PROMPT="$(cat <<EOF
Read AGENTS.md first.
Then run this task file exactly:

$TASK_FILE

Important:
- Follow AGENTS.md.
- Do not commit.
- Do not tag.
- Do not push.
- Write the requested report to the Obsidian vault if the task asks for it.
- At the end, update docs/agents/agent_queue.json:
  - mark the completed task as completed if successful
  - mark it as blocked if validation fails
  - add a concise next task only if clearly necessary
- Stop after this task.
EOF
)"

codex exec --cd "$PROJECT_ROOT" "$PROMPT"
