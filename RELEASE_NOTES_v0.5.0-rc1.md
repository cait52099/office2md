# office2md v0.5.0-rc1 Release Notes

Status: release candidate for v0.5.0.

## Scope

v0.5.0-rc1 adds a read-only MCP adapter foundation over the existing Agent Gateway:

- optional `office2md.mcp_adapter` module;
- MCP wrapper functions:
  - `kb_list`;
  - `kb_context`;
  - `kb_review`;
- optional FastMCP server factory when the `mcp` package is installed;
- docs for read-only MCP architecture and usage;
- tests for wrapper behavior and multi-library provenance.

## Adapter Behavior

The adapter wraps existing gateway helpers:

- `office2md.kb_gateway.kb_list`;
- `office2md.kb_gateway.kb_context`;
- `office2md.kb_gateway.kb_review`.

It does not duplicate search, context, status, or update logic.

The wrapper functions are importable without the optional MCP package installed. Running the server requires the optional `mcp` package:

```powershell
python -m office2md.mcp_adapter
```

## Exposed Tools

The adapter exposes only:

- `kb_list`;
- `kb_context`;
- `kb_review`.

`kb_context` returns `office2md.agent_context.v1`-compatible context with per-library provenance:

- `library_id`;
- `library_name`;
- `library_path`;
- `source_file`;
- `locator`;
- `chunk_id`;
- `document_id`.

`kb_review` remains dry-run/review only and does not execute updates.

## Safety

The adapter does not:

- expose unrestricted SQL;
- execute shell commands;
- modify source files;
- modify conversion output;
- modify library DB, index, graph, or evidence;
- modify source registry, library state, change plan, or update result files;
- auto-update stale libraries;
- delete evidence;
- start a watcher or background process.

## Non-Goals

This release candidate does not include:

- conversion behavior changes;
- build-library behavior changes;
- update-library execution semantic changes;
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

- `kb_list` wrapper returns JSON-compatible catalog output;
- `kb_context` wrapper with one library returns `office2md.agent_context.v1`;
- `kb_context` wrapper with two libraries preserves provenance;
- `kb_review` wrapper returns review JSON without writing `update_result.json`.

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
- MCP adapter import check
