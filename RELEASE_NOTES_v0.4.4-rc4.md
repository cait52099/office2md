# office2md v0.4.4-rc4 Release Notes

Status: release candidate for v0.4.4 agent JSON contract consistency audit.

## Scope

v0.4.4-rc4 is a docs-only checkpoint for agent-ready JSON contract consistency:

- schema/version naming audit for current agent-facing JSON commands;
- clarification of legacy JSON export status for `search-library` and `library-report`;
- agent workflow examples for search, chunk opening, document location, and report context drafting.

## Schema Consistency

The docs now distinguish implemented v0.4.4 schemas from legacy exports:

- `open-chunk --export-json` uses `schema_version: office2md.open_chunk.v1`;
- `locate-document --export-json` uses `schema_version: office2md.locate_document.v1`;
- `build-report-context --export-json` uses `schema_version: office2md.report_context.v1`;
- `search-library --export-json` remains a legacy export without a schema identifier;
- `library-report --export-json` remains a legacy export without a schema identifier.

Future schema polish for `search-library` and `library-report` is documented as additive only and must not change search ranking, search fallback behavior, or report scoring.

## Agent Workflow Examples

The usage docs now include clearer examples for:

- `search-library -> open-chunk -> evidence-first answer`;
- `locate-document -> open-chunk`;
- `build-report-context -> report draft`.

The docs emphasize that agents should cite `source_file`, `locator`, and `chunk_id`, and should preserve limitations and warnings instead of overstating evidence.

## Non-Goals

This checkpoint does not include:

- runtime code changes;
- CLI behavior changes;
- JSON payload structure changes;
- conversion behavior changes;
- build-library behavior changes;
- search ranking, alias, or token fallback changes;
- locate-document matching changes;
- runner changes;
- workspace changes;
- GUI changes;
- incremental update implementation;
- MCP implementation;
- embeddings or vector search;
- OCR;
- Obsidian plugin;
- write-back;
- unrestricted SQL;
- shell execution.

OfficeCLI remains `diagnostic_only`. This checkpoint does not add OfficeCLI sidecar extraction, `--office-engine officecli`, or main conversion pipeline integration.

## Validation

- `python -m pytest`
- `python -m ruff check .`
- `python -m office2md.cli --help`
- `python -m office2md.cli search-library --help`
- `python -m office2md.cli open-chunk --help`
- `python -m office2md.cli locate-document --help`
- `python -m office2md.cli build-report-context --help`
- `python -m office2md.cli library-report --help`
