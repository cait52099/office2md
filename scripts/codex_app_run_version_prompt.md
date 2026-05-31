Read AGENTS.md first.
Then read docs/agents/version_workflow.md.
Then read docs/agents/version_queue.json.
Then run the active version workflow.

Important paths:
- Workspace root: /Volumes/seagate 2t/offic2md
- Repo root: /Volumes/seagate 2t/offic2md/repo
- Obsidian vault: /Volumes/seagate 2t/offic2md/office2md-vault

Rules:
- Complete the active version goal using the file-driven workflow.
- Plan tasks if needed.
- Execute only scoped tasks.
- Validate after changes.
- Perform final review.
- If and only if all validation and smoke checks pass, create one final local commit.
- Do not create checkpoint commits.
- Do not tag.
- Do not push.
- Do not modify source files or Knowledge Packs.
- Stop and report if the workflow becomes ambiguous or validation fails.

At the end:
- update docs/agents/version_queue.json
- write the requested final report to the Obsidian vault
- report files changed, validation, smoke, final commit hash if committed, git status, and confirm no tag/push
