Read AGENTS.md first.

Then run the first ready task from:

docs/agents/agent_queue.json

For the current queue, this should be:

docs/agents/tasks/0002_restore_macos_validation_baseline.md

Important:
- Follow AGENTS.md.
- Follow the task file exactly.
- This is an Execution Agent task.
- Do not commit.
- Do not tag.
- Do not push.
- Stop after this task.
- Write the requested report to the Obsidian vault.
- At the end, update docs/agents/agent_queue.json:
  - mark task 0002 as completed if validation passes
  - mark task 0002 as blocked if validation fails
  - add a concise next task only if clearly necessary

Project root:
/Volumes/seagate 2t/offic2md

Obsidian vault:
/Volumes/seagate 2t/offic2md/office2md-vault
