# office2md v0.4.9-rc1 Release Notes

Status: release candidate for v0.4.9.

## Scope

v0.4.9-rc1 adds Agent Gateway Simplification:

- `kb-list` CLI for listing registered Knowledge Libraries from a catalog;
- `kb-context` CLI for building one agent-facing evidence context packet;
- `kb-review` CLI for read-only update readiness review;
- `office2md.kb_gateway` read-only orchestration helper;
- agent context JSON schema `office2md.agent_context.v1`;
- docs and tests for gateway behavior and multi-library provenance.

## Agent Gateway

The gateway is an orchestration layer over existing office2md contracts. It does not replace the single-library commands.

```powershell
python -m office2md.cli kb-list libraries.json --json
python -m office2md.cli kb-context libraries.json "vacuum pump fault" --library cml125
python -m office2md.cli kb-context libraries.json "pump" --libraries lib-a,lib-b
python -m office2md.cli kb-review libraries.json cml125
```

`kb-context` returns evidence/context only. It does not generate final AI answers.

## Provenance

Every evidence item includes library provenance where available:

- `library_id`;
- `library_name`;
- `library_path`;
- `source_file`;
- `locator`;
- `chunk_id`;
- `document_id`;
- `document_title`;
- `document_kind`;
- `evidence_type`;
- `confidence`;
- `limitation`.

Multi-library context preserves per-library provenance and keeps existing per-library search behavior.

## Read-Only Behavior

`kb-context` checks library freshness and returns stale or unknown status warnings and `next_steps`. It never auto-updates a library.

`kb-review` performs review/dry-run planning only. It does not execute updates, does not run conversion, and does not modify source files or library outputs.

## Non-Goals

This release candidate does not include:

- MCP implementation;
- multi-library ranking replacement;
- conversion behavior changes;
- build-library behavior changes;
- update-library execution semantic changes;
- source registry, library state, change plan, or update result schema breaking changes;
- search ranking, alias, or token fallback changes;
- open-chunk, locate-document, or build-report-context JSON behavior changes;
- runner, workspace, or GUI behavior changes;
- OfficeCLI main-pipeline integration;
- embeddings or vector search;
- OCR;
- Obsidian plugin;
- write-back;
- unrestricted SQL;
- shell execution;
- automatic update, deletion, watcher, or background process.

OfficeCLI remains `diagnostic_only`.

## Smoke

Temp smoke with two tiny libraries and a temp catalog confirmed:

- `kb-list --json` parses;
- `kb-context` with one library parses and includes provenance;
- `kb-context` with two libraries parses and includes per-library provenance;
- `kb-review` parses and remains review-only.

## Validation

- `python -m pytest`
- `python -m ruff check .`
- `python -m compileall office2md/gui`
- `python -m office2md.cli --help`
- `python -m office2md.cli kb-list --help`
- `python -m office2md.cli kb-context --help`
- `python -m office2md.cli kb-review --help`
- `python -m office2md.cli library-catalog --help`
- `python -m office2md.cli search-library --help`
- `python -m office2md.cli open-chunk --help`
