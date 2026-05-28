# office2md v0.4.4-rc1 Release Notes

Status: release candidate for v0.4.4 docs-only foundation.

## Scope

v0.4.4-rc1 documents the Agent-ready JSON Contract Foundation for future read-only AI-agent workflows.

This checkpoint is docs-only. It does not change runtime code, CLI behavior, conversion, build-library, search ranking, search aliases, token fallback, runner behavior, workspace behavior, GUI behavior, or OfficeCLI integration status.

## Agent-Ready JSON Contract

The design establishes CLI/core JSON contract principles:

- agent-facing outputs should be evidence-first;
- JSON contracts should be stable, versioned, and additive;
- CLI JSON is the durable base contract;
- future MCP should be a read-only adapter over the same helpers;
- core helpers should support CLI, GUI, tests, and future MCP without hidden behavior;
- warnings and limitations should be explicit.

## Evidence Packet

The design defines the common evidence packet fields:

- `source_file`
- `locator`
- `chunk_id`
- `document_id`
- `document_title`
- `document_kind`
- `evidence_type`
- `confidence`
- `limitation`

These fields are intended to let agents cite source files, locators, and chunk IDs before drafting answers or reports.

## Planned Schemas

The design documents planned schema/version naming for:

- `office2md.search_results.v1`
- `office2md.open_chunk.v1`
- `office2md.locate_document.v1`
- `office2md.report_context.v1`
- `office2md.library_report.v1`

## Planned Workflows

The usage doc covers planned workflows:

- search -> open-chunk -> evidence-first answer;
- locate-document -> open-chunk;
- build-report-context -> report draft.

## Non-Goals

This checkpoint does not include:

- MCP implementation;
- embeddings or vector search;
- OCR;
- Obsidian plugin;
- write-back;
- unrestricted SQL;
- shell execution;
- conversion/build-library/search/ranking/runner/workspace/GUI behavior changes.

OfficeCLI remains `diagnostic_only`. This release does not recommend OfficeCLI sidecar extraction, `--office-engine officecli`, or main conversion pipeline integration.

## Validation

- `python -m pytest`
- `python -m ruff check .`
- `python -m office2md.cli --help`

