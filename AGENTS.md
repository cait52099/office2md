# AGENTS.md — office2md

## 1. Project Identity

office2md is a local evidence-first knowledge backend for AI agents.

It converts raw documents into Knowledge Packs, builds a local library, exposes stable CLI JSON contracts, and supports read-only agent access through CLI helpers and a read-only MCP adapter.

Core direction:

```text
Raw documents
→ office2md convert
→ Knowledge Packs
→ build-library
→ library.db / library_index.json / library_graph.json
→ stable CLI JSON contracts
→ read-only agent interface
→ evidence-first reports, troubleshooting packages, SOP impact summaries, supplier email drafts
```

office2md should remain the knowledge backend.

Obsidian, VS Code, Foam, MkDocs, or other tools may be useful human-facing frontends, but they must not become the core architecture.

---

## 2. Default Local Paths

Default local workspace root may be:

```text
/Volumes/seagate 2t/offic2md
```

Default local repository root may be:

```text
/Volumes/seagate 2t/offic2md/repo
```

Default Obsidian project journal may be:

```text
/Volumes/seagate 2t/offic2md/office2md-vault
```

Do not assume these paths are valid without checking.

---

## 3. Architecture Principles

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
- read-only MCP adapter

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

This project uses separate planning/review agents and execution agents.

### 5.1 Planning / Review Agent

Responsibilities:
- understand the project direction
- review architecture and reports
- create optimization plans
- split work into small execution tasks
- decide whether work is ready for checkpoint or release
- write concise notes to the Obsidian project journal when a vault path is provided
- prepare exact task files for Execution Agents

The Planning / Review Agent should not implement code changes unless explicitly asked.

The Planning / Review Agent should not commit or tag.

### 5.2 Execution Agent

Responsibilities:
- execute one clearly scoped task only
- follow the task file and this AGENTS.md
- make minimal code, doc, and test changes
- run validation and smoke tests
- report files changed, implementation summary, tests, validation, smoke result, git status, and readiness

The Execution Agent must not:
- decide the next roadmap item
- expand scope
- commit or tag unless explicitly asked
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
- commit and create annotated tag only when explicitly requested and review passes

### 5.4 Final Release Agent

Responsibilities:
- run final release readiness review
- confirm no blockers
- confirm version metadata
- confirm release notes and checklist
- run validation
- create final release commit and annotated tag only when explicitly requested

The Final Release Agent must not add new features.

---

## 6. Semi-automated Workflow Rule

The preferred workflow is file-driven and repeatable.

Use `docs/agents/agent_queue.json` and `docs/agents/tasks/` to coordinate planning, execution, review, and release.

Typical flow:

```text
Planning Agent
→ writes next task file in docs/agents/tasks/
→ updates docs/agents/agent_queue.json
→ Execution Agent runs exactly one task file
→ writes report to Obsidian vault and docs/agents/reports/ if requested
→ Review / Checkpoint Agent reviews result
→ Planning Agent decides next task
```

Fresh execution context is required for each new optimization task. If a platform cannot automatically create a new agent/session, simulate freshness by starting from the task file only and not relying on previous chat context.

Human approval is required before:
- commit
- tag
- push
- final release
- real-source full conversion
- behavior changes in protected areas

---

## 7. Hard Non-goals

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

## 8. Protected Behaviors

Do not change these unless the task explicitly says so:

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

## 9. OfficeCLI Policy

OfficeCLI is optional and diagnostic only.

It may be used for benchmark or comparison tasks only.

Do not:
- add OfficeCLI as a required dependency
- make OfficeCLI the default conversion engine
- integrate OfficeCLI into the main conversion pipeline
- add OfficeCLI sidecar extraction
- add `--office-engine officecli`

Current recommendation:
- diagnostic_only

Reason:
- read-only safety appears good
- command timeouts still exist on some files
- benchmark evidence does not justify main-pipeline integration

---

## 10. Obsidian Project Journal Workflow

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
- do not modify Obsidian notes unless explicitly asked or task file provides a target path
- do not treat Obsidian notes as raw evidence
- do not use Obsidian as the core data layer
- do not run shell commands from Obsidian unless explicitly asked
- keep notes concise
- prefer append-only decision logs
- when writing reports, include date, task name, scope, validation, smoke result, and next recommendation

---

## 11. Standard Validation

Run when possible:

```bash
python -m pytest
python -m ruff check .
python -m compileall office2md/gui
python -m office2md.cli --help
```

Relevant CLI help checks may include:

```bash
python -m office2md.cli convert --help
python -m office2md.cli build-library --help
python -m office2md.cli search-library --help
python -m office2md.cli locate-document --help
python -m office2md.cli open-chunk --help
python -m office2md.cli build-report-context --help
python -m office2md.cli scan-changes --help
python -m office2md.cli library-status --help
python -m office2md.cli source-registry --help
python -m office2md.cli update-library --help
python -m office2md.cli library-catalog --help
python -m office2md.cli kb-list --help
python -m office2md.cli kb-context --help
python -m office2md.cli kb-review --help
```

If only docs changed, still run at least:

```bash
python -m pytest
python -m ruff check .
```

---

## 12. Smoke Test Principles

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

## 13. JSON Contract Rules

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

---

## 14. Git Rules

Default:
- do not commit
- do not tag
- do not push

Only commit or tag when the task explicitly asks for checkpoint or release.

Before any commit:
- inspect git diff
- run validation
- update release notes/checklist if scoped
- confirm git status
- confirm no unrelated files are included

Checkpoint commit message format:

```text
Release <tag>
```

Use annotated tags for checkpoints and releases.

---

## 15. Report Style

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
