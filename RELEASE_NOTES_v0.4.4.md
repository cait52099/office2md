# office2md v0.4.4 Release Notes

Status: final v0.4.4 release.

## Scope

v0.4.4 establishes the Agent-ready JSON Contract Foundation:

- Agent-ready JSON contract design and usage docs;
- `open_chunk()` core helper;
- `open-chunk` read-only CLI;
- `locate-document --export-json`;
- `build-report-context` read-only CLI;
- evidence-first agent workflow examples;
- schema/version consistency audit.

## Agent-Ready JSON Commands

`open-chunk` opens a chunk by exact `chunk_id` and can include same-document context:

```powershell
python -m office2md.cli open-chunk LIBRARY_DIR CHUNK_ID --context 2 --export-json open_chunk.json
```

The JSON schema is `office2md.open_chunk.v1`.

`locate-document` can export matches as JSON:

```powershell
python -m office2md.cli locate-document LIBRARY_DIR QUERY --export-json locate.json
```

The JSON schema is `office2md.locate_document.v1`. Matching, ordering, and limits are unchanged.

`build-report-context` builds a read-only evidence package for agent report drafting:

```powershell
python -m office2md.cli build-report-context LIBRARY_DB QUERY --context 2 --export-json report_context.json
```

The JSON schema is `office2md.report_context.v1`. The command reuses existing search, context, and diagnostics helpers without changing ranking, aliases, token fallback, or matching behavior.

## Evidence-First Fields

The agent-ready docs define evidence packet fields including:

- `source_file`;
- `locator`;
- `chunk_id`;
- `document_id`;
- `document_title`;
- `document_kind`;
- `evidence_type`;
- `confidence`;
- `limitation`.

Agent workflow examples cover:

- `search-library -> open-chunk -> evidence-first answer`;
- `locate-document -> open-chunk`;
- `build-report-context -> report draft`.

## Legacy JSON Exports

`search-library --export-json` and `library-report --export-json` remain legacy exports without schema identifiers in v0.4.4.

Future schema polish for these exports should be additive only and must not change search ranking, search fallback behavior, or library report scoring.

## Non-Goals

This release does not include:

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

OfficeCLI remains `diagnostic_only`. This release does not add OfficeCLI sidecar extraction, `--office-engine officecli`, or main conversion pipeline integration.

## Validation

- `python -m pytest`
- `python -m ruff check .`
- `python -m compileall office2md/gui`
- `python -m office2md.cli --help`
- `python -m office2md.cli search-library --help`
- `python -m office2md.cli open-chunk --help`
- `python -m office2md.cli locate-document --help`
- `python -m office2md.cli build-report-context --help`
- `python -m office2md.cli library-report --help`
- `python -m office2md.cli officecli-benchmark --help`
- `python -m office2md.cli workspace-status --help`
