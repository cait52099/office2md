#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VERSION_QUEUE="$REPO_ROOT/docs/agents/version_queue.json"
PROMPT_FILE="$REPO_ROOT/scripts/codex_app_run_version_prompt.md"

cd "$REPO_ROOT"

if ! command -v codex >/dev/null 2>&1; then
  echo "ERROR: codex CLI not found."
  echo "Use Codex App with scripts/codex_app_run_version_prompt.md instead."
  exit 1
fi

if [ ! -f "$VERSION_QUEUE" ]; then
  echo "ERROR: missing $VERSION_QUEUE"
  exit 1
fi

if [ ! -f "$PROMPT_FILE" ]; then
  echo "ERROR: missing $PROMPT_FILE"
  exit 1
fi

python3 - <<'PY'
import json
from pathlib import Path
q = json.loads(Path('docs/agents/version_queue.json').read_text(encoding='utf-8'))
active = q.get('active_version') or {}
if active.get('allow_tag') or active.get('allow_push'):
    raise SystemExit('Refusing to run: version queue allows tag or push')
if not active.get('allow_final_commit'):
    raise SystemExit('Refusing to run: allow_final_commit is false')
print(f"Active version: {active.get('version')} status={active.get('status')}")
PY

PROMPT="$(cat "$PROMPT_FILE")"

codex exec --cd "$REPO_ROOT" --sandbox workspace-write "$PROMPT"
