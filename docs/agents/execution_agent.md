# Execution Agent Workflow

Use this guide when running one queued office2md task in Codex App or the Codex CLI.

## Local Paths

- Workspace root: `/Volumes/seagate 2t/offic2md`
- Repository root: `/Volumes/seagate 2t/offic2md/repo`
- Obsidian vault: `/Volumes/seagate 2t/offic2md/office2md-vault`

Check paths before relying on them. The repository root is where `AGENTS.md`, `docs/agents/agent_queue.json`, task files, source code, and validation commands live.

## Run One Task

1. Read `AGENTS.md`.
2. Read `docs/agents/agent_queue.json`.
3. Select the first task with `status: ready_for_execution`.
4. Read only that task file under `docs/agents/tasks/`.
5. Execute only the scoped task.
6. Run the validation and smoke checks required by the task.
7. Write the requested report, usually under the Obsidian vault.
8. Update `docs/agents/agent_queue.json` for that task:
   - use `completed` when validation passes
   - use `blocked` when validation fails
   - do not add a next task unless the task explicitly asks for one or it is clearly necessary

Stop after one task.

## Safety Boundaries

- Do not commit, tag, or push unless the task explicitly asks and human approval is present.
- Do not change product runtime behavior unless the task explicitly scopes it.
- Do not modify source documents or Knowledge Packs unless explicitly scoped.
- Keep workflow edits separate from product feature changes.

## Codex App Prompt

For Codex App, paste `scripts/codex_app_run_next_prompt.md`. It intentionally points Codex at the queue instead of naming a specific task, so it stays reusable after each completed task.

## Codex CLI Helper

From the repository root, `scripts/agent_run_next.sh` runs the first ready task through the Codex CLI when `codex` is available. The helper derives the default repository root from its own location and respects a `PROJECT_ROOT` environment override.
