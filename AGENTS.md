# AGENTS.md — office2md

## 1. Project Identity

office2md is a local evidence-first knowledge backend for AI agents.

It converts raw documents into Knowledge Packs, builds a local library, exposes stable CLI JSON contracts, and supports read-only agent access through CLI helpers and a future/read-only MCP adapter.

Core direction:

Raw documents  
→ office2md convert  
→ Knowledge Packs  
→ build-library  
→ library.db / library_index.json / library_graph.json  
→ stable CLI JSON contracts  
→ read-only agent interface  
→ evidence-first reports, troubleshooting packages, SOP impact summaries, supplier email drafts, and evidence packages.

office2md should remain the knowledge backend.

Obsidian, VS Code, Foam, MkDocs, or other tools may be useful human-facing frontends, but they must not become the core architecture.

---

## 2. Local Path Model

This project may be used in a local workspace with three separate paths.

### Workspace root

```text
/Volumes/seagate 2t/offic2md
```

The workspace root may contain the Git repo, Obsidian vault, temporary files, and local workflow helpers.

### Git repo / project root

```text
/Volumes/seagate 2t/offic2md/repo
```

This is the real office2md Git repository.

All code, tests, docs, release files, commits, and version workflow changes must happen here.

### Obsidian project journal

```text
/Volumes/seagate 2t/offic2md/office2md-vault
```

This is the human-facing project journal.

It is not the Git repo and not the core knowledge backend.

Do not confuse the workspace root with the Git repo.

When running Git commands, validation, tests, commits, or release workflow, use the Git repo path.

---

## 3. Core Architecture Principles

office2md should grow as a four-layer local knowledge system.

### 3.1 Raw Evidence Layer

Includes:

- raw documents
- Knowledge Packs
- library.db
- source locators
- source checksums
- traceability manifests

Rules:

- do not modify source files
- do not automatically modify Knowledge Packs unless explicitly scoped
- preserve source traceability
- preserve source checksum safety

### 3.2 Understanding Layer

Includes future human-editable:

- wiki notes
- corrections
- process understanding
- decision notes

Rules:

- must remain linked back to evidence
- must not replace raw evidence
- must not become untraceable AI-generated truth

### 3.3 Agent Interface Layer

Includes:

- stable CLI JSON contracts
- read-only helper functions
- future/read-only MCP adapter

Rules:

- prefer stable JSON schemas
- keep interfaces read-only unless explicitly scoped
- no unrestricted SQL
- no shell execution through agent interfaces
- no write-back by default

### 3.4 Output Layer

Includes:

- reports
- supplier email drafts
- SOP impact summaries
- troubleshooting packages
- evidence packages

Rules:

- outputs should cite evidence
- evidence should include source_file, locator, chunk_id, document_id, document_title, and library provenance when applicable
- weak or missing evidence must be stated clearly

---

## 4. Evidence-first Rule

For factual claims from the knowledge base, outputs should include:

- source_file
- locator
- chunk_id
- document_id
- document_title
- confidence or limitation
- library_id, library_name, and library_path when using multi-library context

Do not answer from memory when office2md evidence is available.

If evidence is missing, weak, stale, outdated, or only partially relevant, say so clearly.

---

## 5. Agent Roles

This project uses separate planning/review agents, execution agents, review/checkpoint agents, final release agents, and version workflow agents.

### 5.1 Planning / Review Agent

Responsibilities:

- understand the project direction
- review architecture and reports
- create optimization plans
- split work into small execution tasks
- decide whether work is ready for checkpoint or release
- write concise notes to the Obsidian project journal when a vault path is provided
- prepare exact prompts or task files for Execution Agents

The Planning / Review Agent should not implement code changes unless explicitly asked.

The Planning / Review Agent should not commit, tag, or push.

### 5.2 Execution Agent

Responsibilities:

- execute one clearly scoped task only
- follow the task prompt and this AGENTS.md
- make minimal code, doc, and test changes
- run validation and smoke tests
- report files changed, implementation summary, tests, validation, smoke result, git status, and readiness

The Execution Agent must not:

- decide the next roadmap item
- expand scope
- commit or tag unless explicitly asked
- push
- perform unrelated cleanup
- change runtime behavior outside the task scope

### 5.3 Review / Checkpoint Agent

Responsibilities:

- review a completed implementation task
- inspect git diff
- confirm scope compliance
- confirm validation and smoke results
- confirm excluded behavior did not change
- create release notes and checklist when scoped
- commit only when explicitly requested
- create annotated tags only when explicitly requested

### 5.4 Final Release Agent

Responsibilities:

- run final release readiness review
- confirm no blockers
- confirm version metadata
- confirm release notes and checklist
- run validation
- create final release commit and annotated tag only when explicitly requested

The Final Release Agent must not add new features.

### 5.5 Version Workflow Agent

Responsibilities:

- execute a complete small-version workflow from a version goal file
- plan internal tasks
- execute bounded changes
- validate all changes
- write Obsidian reports
- create one final local version commit if all validation passes and policy allows

The Version Workflow Agent must not:

- create checkpoint commits
- create tags
- push
- run unbounded optimization
- modify source documents
- modify Knowledge Packs unless explicitly scoped
- continue if validation fails
- continue if scope becomes unclear

---

## 6. Fresh Execution Context Rule

Use a fresh execution agent/session for each new optimization task when working in manual task mode.

Reason:

- avoid context pollution
- avoid scope drift
- reduce token usage
- improve review clarity
- make each change easier to validate and checkpoint

Each execution task must be self-contained and include:

- current checkpoint or current version
- task name
- exact scope
- explicit non-goals
- files likely involved if known
- validation commands
- smoke tests
- required report format

Do not continue from a previous execution session for a new optimization task unless explicitly requested.

---

## 7. Version Workflow Policy

This project may use a complete small-version workflow.

Goal:

- complete one small version from planning to implementation, validation, review, and final local commit
- reduce manual prompts
- preserve safety
- avoid tag/push unless explicitly requested

Default mode:

```text
planning → execution → validation → review → one final local commit
```

Default policy:

- final commit allowed only if explicitly enabled in `docs/agents/version_queue.json`
- tag disabled by default
- push disabled by default
- checkpoint commits disabled by default
- final commit only after validation passes
- stop if blockers are found

The version workflow is driven by:

```text
docs/agents/version_queue.json
docs/agents/tasks/VERSION_GOAL_<version>.md
scripts/codex_app_run_version_prompt.md
scripts/agent_run_version.sh
```

### 7.1 Version Queue Rules

The version queue should use a machine-readable JSON file:

```text
docs/agents/version_queue.json
```

The queue should define:

- target version
- version goal file
- allowed commit policy
- tag policy
- push policy
- validation requirements
- report paths

Default safe policy:

```json
{
  "allow_final_commit": true,
  "allow_tag": false,
  "allow_push": false,
  "commit_policy": "final_only"
}
```

### 7.2 Version Goal Rules

Each small version should have a self-contained goal file:

```text
docs/agents/tasks/VERSION_GOAL_vX.Y.Z.md
```

The goal file should include:

- version
- goal
- why it matters
- scope
- non-goals
- protected behaviors
- allowed files or areas
- validation commands
- smoke tests
- Obsidian report path
- final commit policy

### 7.3 Commit-only Version Rule

When the user asks for a complete small-version workflow that “only commits”:

Allowed:

- implement scoped changes
- update tests
- update docs
- update release notes or version notes when scoped
- run validation
- create one final local commit

Not allowed:

- tag
- push
- checkpoint commit
- release tag
- source document modification
- Knowledge Pack modification
- unbounded refactor
- unrelated cleanup

Final commit message should usually be:

```text
Complete <version> workflow
```

or, if the user asks for release-style naming:

```text
Release <version>
```

Do not create a tag unless the user explicitly asks.

Do not push unless the user explicitly asks.

### 7.4 Stop Conditions

The version workflow must stop without committing if:

- validation fails
- git diff includes unexpected files
- scope becomes unclear
- product runtime behavior changes outside the version goal
- source files were modified
- Knowledge Packs were modified without explicit permission
- tests cannot run and no acceptable reason is documented
- required report files cannot be written
- tag or push would be required but is not explicitly allowed

### 7.5 Codex App Version Workflow

When using Codex App, run the version workflow by opening the Git repo:

```text
/Volumes/seagate 2t/offic2md/repo
```

Then execute:

```text
Read scripts/codex_app_run_version_prompt.md and execute it.
```

The prompt should read:

- `AGENTS.md`
- `docs/agents/version_workflow.md`
- `docs/agents/version_queue.json`
- the active version goal file

The Codex App workflow should complete the version if safe, then stop.

### 7.6 Codex CLI Version Workflow

When Codex CLI is available, the version workflow may be run with:

```bash
cd "/Volumes/seagate 2t/offic2md/repo"
./scripts/agent_run_version.sh
```

The script must refuse to run if:

- tag is allowed by default
- push is allowed by default
- queue file is missing
- version goal file is missing
- policy is unsafe

### 7.7 Optimizer Loop Mode

This project may use `mode: optimizer_loop` in `docs/agents/version_queue.json`.

Purpose:

- run one complete small-version improvement loop: `CHECK -> PLAN -> OPTIMIZE -> REVIEW -> COMMIT -> STOP`
- improve ongoing office2md optimization and correction
- improve user friendliness, efficiency, bug reduction, agent workflow usability, large-folder update workflow, JSON contract clarity, and source-file safety

Default rules:

- select at most one P1 task per loop
- keep the task small and bounded
- prefer low-risk docs, workflow, CLI help, validation, and UX improvements before deeper runtime changes
- create exactly one final local commit only if validation passes and policy allows it
- do not create tags
- do not push
- stop after the commit

The optimizer loop must not:

- run multiple loops in one invocation
- perform broad refactors
- modify source documents
- modify Knowledge Packs without explicit permission
- add AI/OCR/embedding/vector/cloud work
- add unrestricted SQL or shell access
- change protected behaviors unless explicitly scoped and tested

Protected behaviors include:

- conversion behavior
- build-library behavior
- search ranking
- search aliases
- token fallback
- runner process-control behavior
- GUI behavior
- Agent Gateway behavior
- MCP adapter behavior

When using Codex App, run:

```text
Read scripts/codex_app_run_version_prompt.md and execute it.
```

When Codex CLI is available, the optimizer loop may be run through the version runner script if the policy is safe.

---

## 8. Automated Runner Policy

Codex may be called by local runner scripts using `codex exec` when available.

The runner may automatically execute tasks only when:

- the task status is `ready_for_execution`
- the task has a task file under `docs/agents/tasks/`
- the task explicitly says not to commit, tag, or push
- the queue policy has `auto_execute_ready_tasks: true`
- `allow_commit`, `allow_tag`, and `allow_push` are all false

The runner must not automatically:

- commit
- tag
- push
- run final release
- run checkpoint release
- modify source documents
- run large real-source conversion unless explicitly requested

After each task, the runner should stop by default.

A human or Planning / Review Agent should review the report before enabling the next task.

For full small-version workflows, use the Version Workflow Policy instead of the single-task runner.

---

## 9. Hard Non-goals

Do not implement unless explicitly requested:

- embeddings or vector search
- OCR
- AI/LLM enrichment
- cloud dependency
- Obsidian plugin
- Obsidian as core architecture
- unrestricted SQL
- shell execution from agent interfaces
- write-back features
- automatic source-file modification
- automatic Knowledge Pack modification
- automatic AI summary cache
- direct SharePoint / Teams API
- OfficeCLI as default conversion engine
- OfficeCLI as required dependency
- OfficeCLI sidecar extraction
- `--office-engine officecli`
- external office2md packages as dependencies
- legacy `.doc` conversion unless explicitly scoped

---

## 10. Protected Behaviors

Do not change these unless the task or version goal explicitly says so:

- conversion behavior
- build-library behavior
- search ranking
- search aliases
- token fallback
- runner process-control behavior
- workspace behavior
- GUI behavior
- Graph View behavior
- Obsidian export behavior
- Agent Gateway behavior
- MCP adapter behavior
- existing JSON schema semantics

If a task requires touching a protected area, clearly state:

- why it is necessary
- what behavior is expected to remain unchanged
- what tests or smoke checks prove it

---

## 11. OfficeCLI Policy

OfficeCLI is optional and diagnostic only.

It may be used for benchmark or comparison tasks only.

Do not:

- add OfficeCLI as a required dependency
- make OfficeCLI the default conversion engine
- integrate OfficeCLI into the main conversion pipeline
- add OfficeCLI sidecar extraction
- add `--office-engine officecli`

Current recommendation:

```text
diagnostic_only
```

Reason:

- read-only safety appears good
- command timeouts still exist on some files
- benchmark evidence does not justify main-pipeline integration

---

## 12. External Packages Policy

Do not add external conversion packages as dependencies unless explicitly approved.

External packages with similar names, including PyPI packages named `office2md`, must be treated as unrelated unless explicitly verified.

External conversion tools may only be used in isolated benchmark environments when explicitly scoped.

Never install benchmark-only external packages into this repository's main virtual environment.

---

## 13. Obsidian Project Journal Workflow

This project may use an Obsidian vault as a human-facing project journal.

Default local vault path may be:

```text
/Volumes/seagate 2t/offic2md/office2md-vault
```

The vault is for:

- project understanding
- review reports
- optimization plans
- decision records
- Codex execution reports
- release notes drafts
- version workflow reports

The vault is not the core knowledge architecture.

office2md remains the local evidence backend.

Recommended folders:

```text
00_Project/
10_Reviews/
20_Plans/
30_Codex_Reports/
40_Decisions/
50_Releases/
```

Rules:

- do not modify Obsidian notes unless explicitly asked or required by the active workflow
- do not treat Obsidian notes as raw evidence
- do not use Obsidian as the core data layer
- do not run shell commands from Obsidian unless explicitly asked
- keep notes concise
- prefer append-only decision logs
- when writing reports, include date, task name, scope, validation, smoke result, and next recommendation

---

## 14. Default Review Workflow

When asked to review the whole project:

1. Check repository status.
2. Confirm current version and tags.
3. Set up or verify local environment if needed.
4. Run validation where possible.
5. Inspect high-level architecture.
6. Review CLI commands and JSON schemas.
7. Review docs and user workflow clarity.
8. Review likely bug risks and user friction.
9. Review agent-readiness and evidence traceability.
10. Recommend small, staged tasks.
11. Write a concise report.
12. Do not implement code changes unless explicitly asked.
13. Do not commit or tag.

---

## 15. Standard Validation

Run when possible:

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
.venv/bin/python -m compileall office2md/gui
.venv/bin/python -m office2md.cli --help
```

If `.venv/bin/python` does not exist, use the project’s active Python interpreter and report which interpreter was used.

Relevant CLI help checks may include:

```bash
.venv/bin/python -m office2md.cli convert --help
.venv/bin/python -m office2md.cli build-library --help
.venv/bin/python -m office2md.cli search-library --help
.venv/bin/python -m office2md.cli locate-document --help
.venv/bin/python -m office2md.cli open-chunk --help
.venv/bin/python -m office2md.cli build-report-context --help
.venv/bin/python -m office2md.cli scan-changes --help
.venv/bin/python -m office2md.cli library-status --help
.venv/bin/python -m office2md.cli source-registry --help
.venv/bin/python -m office2md.cli update-library --help
.venv/bin/python -m office2md.cli library-catalog --help
.venv/bin/python -m office2md.cli kb-list --help
.venv/bin/python -m office2md.cli kb-context --help
.venv/bin/python -m office2md.cli kb-review --help
```

If GUI code changed, run:

```bash
.venv/bin/python -m compileall office2md/gui
```

If only docs changed, still run at least:

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
```

For workflow-only changes, also run:

```bash
.venv/bin/python -m json.tool docs/agents/agent_queue.json
.venv/bin/python -m json.tool docs/agents/version_queue.json
bash -n scripts/agent_run_next.sh
bash -n scripts/agent_run_version.sh
```

Only run checks for files that exist.

---

## 16. Smoke Test Principles

Smoke tests should be small, safe, and task-specific.

Prefer:

- temporary folders
- tiny sample libraries
- dry-run workflows
- export-json parsing
- read-only source checks
- CLI help checks
- schema checks

Avoid:

- large real-source conversion unless explicitly requested
- modifying user source folders
- deleting existing evidence
- long-running uncontrolled conversions
- network-dependent smoke tests

For real-source smoke tests:

- source folder must remain unchanged
- use temp output folders
- prefer dry-run first
- report file counts and classification counts
- report whether source files changed

---

## 17. JSON Contract Rules

For agent-facing JSON:

- include a schema identifier when introducing new contracts
- keep fields stable and additive when possible
- avoid breaking existing consumers
- use UTF-8 output
- prefer `--export-json` for large output
- keep console JSON Windows-safe when relevant
- include warnings and next_steps when status is stale, unknown, partial, or unsafe

Evidence-bearing JSON should preserve:

- source_file
- locator
- chunk_id
- document_id
- document_title
- library_id / library_name / library_path when applicable

Workflow JSON should be machine-readable and stable enough for scripts:

- `docs/agents/agent_queue.json`
- `docs/agents/version_queue.json`

---

## 18. Git Rules

Default:

- do not commit
- do not tag
- do not push

Only commit when the task or version workflow explicitly allows it.

Only tag when the user explicitly asks.

Only push when the user explicitly asks.

Before any commit:

- inspect git diff
- run validation
- confirm no unrelated files are included
- confirm source files were not modified
- confirm protected behaviors remain unchanged unless scoped
- update report files when required

Checkpoint commit message format when checkpointing is explicitly allowed:

```text
Release <tag>
```

Small-version workflow final commit message format when commit-only workflow is explicitly allowed:

```text
Complete <version> workflow
```

or, if requested:

```text
Release <version>
```

Annotated tags are allowed only when explicitly requested.

---

## 19. Report Format for Planning / Review

Use this concise format:

```md
# office2md Planning / Review Report

## 1. Context
- Project root:
- Workspace root:
- Obsidian vault:
- Current version/tag:
- Git status:
- Task:

## 2. Current Understanding
Short summary.

## 3. Findings
### User Friendliness
- Finding:
- Impact:
- Recommendation:

### Efficiency
- Finding:
- Impact:
- Recommendation:

### Reliability / Bug Risk
- Finding:
- Impact:
- Recommendation:

### Agent-readiness
- Finding:
- Impact:
- Recommendation:

## 4. Recommended Next Tasks
### P1
1.
2.

### P2
1.
2.

### Do Not Do Now
1.
2.

## 5. Suggested Next Execution Prompt or Task File
Include a self-contained prompt or task file path for the next Execution Agent.
```

---

## 20. Report Format for Execution Agent

Use this concise format:

```md
# office2md Execution Report

## 1. Task
- Current checkpoint/version:
- Task:
- Scope:

## 2. Files Changed
-

## 3. Implementation Summary
-

## 4. Tests Added or Updated
-

## 5. Validation
- pytest:
- ruff:
- compileall:
- CLI help:
- JSON/script checks:

## 6. Smoke
-

## 7. Behavior Boundaries
Confirm unchanged unless task-specific:
- conversion:
- build-library:
- search/ranking:
- runner:
- workspace:
- GUI:
- Agent Gateway / MCP:
- source files:
- Knowledge Packs:

## 8. Git Status
-

## 9. Readiness
Ready for review/checkpoint:
Yes/No

Reason:
-
```

---

## 21. Report Format for Review / Checkpoint Agent

Use this concise format:

```md
# office2md Review / Checkpoint Report

## 1. Task
- Previous checkpoint:
- New commit/tag if any:
- Task reviewed:

## 2. Review Summary
-

## 3. Scope Confirmation
-

## 4. Validation
- pytest:
- ruff:
- compileall:
- CLI help:
- JSON/script checks:

## 5. Smoke
-

## 6. Release Docs
- RELEASE_NOTES:
- RELEASE_CHECKLIST:

## 7. Commit / Tag
- Commit:
- Tag:

## 8. Git Status
-

## 9. Next Recommendation
-
```

---

## 22. Report Format for Final Release Agent

Use this concise format:

```md
# office2md Final Release Report

## 1. Release
- Latest RC:
- Final version:
- Git status before:

## 2. Blockers
- None / list blockers

## 3. Final Scope
-

## 4. Explicit Non-goals
-

## 5. Version Metadata
- pyproject.toml:
- office2md.__version__:

## 6. Validation
- pytest:
- ruff:
- compileall:
- CLI help:
- JSON/script checks:

## 7. Smoke
-

## 8. Final Commit / Tag
- Commit:
- Tag:

## 9. Git Status After
-

## 10. Push Status
- Performed / not performed

## 11. Recommended Next Direction
-
```

---

## 23. Report Format for Version Workflow Agent

Use this concise format:

```md
# office2md Version Workflow Report

## 1. Version
- Version:
- Goal file:
- Project root:
- Workspace root:
- Obsidian vault:

## 2. Policy
- Final commit allowed:
- Tag allowed:
- Push allowed:
- Commit policy:

## 3. Scope
-

## 4. Work Completed
-

## 5. Files Changed
-

## 6. Tests Added or Updated
-

## 7. Validation
- pytest:
- ruff:
- compileall:
- CLI help:
- JSON/script checks:

## 8. Smoke
-

## 9. Protected Behavior Confirmation
- conversion:
- build-library:
- search/ranking:
- runner:
- workspace:
- GUI:
- Agent Gateway / MCP:
- source files:
- Knowledge Packs:

## 10. Commit
- Commit created:
- Commit hash:
- Commit message:

## 11. Tag / Push
- Tag created:
- Push performed:

## 12. Git Status
-

## 13. Next Recommendation
-
```

---

## 24. Task Sizing Rule

Prefer small tasks.

A good execution task should usually:

- touch a small number of files
- have clear tests
- have clear smoke checks
- avoid changing multiple subsystems
- be reviewable in one checkpoint

If a task affects many areas, split it.

For version workflow mode, the version may contain multiple internal steps, but the total scope must still remain small and bounded.

---

## 25. Default Priority Order

When optimizing the whole project, prioritize:

1. source-file safety
2. evidence traceability
3. stable JSON contracts
4. dry-run and review workflows
5. large-folder update reliability
6. user-friendly CLI help and docs
7. agent-readiness
8. GUI polish
9. optional adapters

Do not prioritize novelty over reliability.

---

## 26. Communication Style

Reports should be:

- concise
- evidence-based
- scoped
- explicit about limitations
- clear about next steps

Avoid:

- broad claims without evidence
- unrelated refactoring
- long speculative roadmaps
- changing behavior without tests
