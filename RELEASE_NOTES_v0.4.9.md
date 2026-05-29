# office2md v0.4.9 Release Notes

Status: final v0.4.9 release.

## Scope

v0.4.9 adds Agent Gateway Simplification:

- read-only `office2md.kb_gateway` helper;
- `kb-list` CLI;
- `kb-context` CLI;
- `kb-review` CLI;
- agent context JSON schema `office2md.agent_context.v1`;
- multi-library context with per-library provenance;
- stale/unknown library warnings and `next_steps`;
- docs and tests for agent gateway workflows.

## Gateway Commands

```powershell
python -m office2md.cli kb-list libraries.json --json
python -m office2md.cli kb-context libraries.json "vacuum pump fault" --library cml125
python -m office2md.cli kb-context libraries.json "pump" --libraries lib-a,lib-b
python -m office2md.cli kb-review libraries.json cml125
```

The gateway simplifies common agent workflows that previously required manually chaining `library-catalog`, `library-status`, `search-library`, `open-chunk`, and report context commands.

## Agent Context

`kb-context` emits schema:

```text
office2md.agent_context.v1
```

Context packets include:

- `request`;
- `selected_libraries`;
- `library_status`;
- `evidence`;
- `supporting_chunks`;
- `limitations`;
- `warnings`;
- `next_steps`.

Every evidence item includes per-library provenance where available:

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

## Read-Only Behavior

`kb-context` checks freshness and reports stale/unknown library warnings, but it never auto-updates.

`kb-review` is review/dry-run only. It does not execute updates, run conversion, or modify sources/libraries.

Existing single-library commands remain compatible.

## Non-Goals

This release does not include:

- conversion behavior changes;
- build-library behavior changes;
- update-library execution semantic changes;
- source registry, library state, change plan, or update result schema breaking changes;
- search ranking, alias, or token fallback changes;
- open-chunk, locate-document, or build-report-context JSON behavior changes;
- runner, workspace, or GUI behavior changes;
- MCP implementation;
- embeddings or vector search;
- OCR;
- Obsidian plugin;
- write-back;
- unrestricted SQL;
- shell execution;
- automatic update;
- automatic deletion;
- watcher or background process.

OfficeCLI remains `diagnostic_only`.

## Smoke

Temp smoke with two tiny libraries and a temp catalog confirmed:

- `kb-list --json` parses;
- `kb-context` with one library parses;
- `kb-context` with two libraries parses;
- `kb-review` parses;
- evidence provenance includes `library_id`, `library_name`, and `library_path`.

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
