# office2md v0.5.0 Release Notes

Status: final v0.5.0 release.

## Scope

v0.5.0 adds a read-only MCP adapter foundation over the Agent Gateway:

- optional `office2md.mcp_adapter` module;
- MCP wrapper functions:
  - `kb_list`;
  - `kb_context`;
  - `kb_review`;
- wrappers call `office2md.kb_gateway`;
- wrapper functions import without the optional MCP package installed;
- FastMCP server starts only when the optional `mcp` package is available;
- docs and tests for read-only MCP usage and safety.

## Tools

The adapter exposes only:

- `kb_list`;
- `kb_context`;
- `kb_review`.

`kb_context` returns `office2md.agent_context.v1`-compatible output and preserves multi-library provenance:

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

- expose SQL;
- execute shell commands;
- write back to source files;
- modify conversion output;
- modify library DB, index, graph, or evidence;
- modify registry, state, change plan, or update result files;
- auto-update stale libraries;
- delete evidence;
- start watchers or background processes.

## Non-Goals

This release does not include:

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
- `kb_review` wrapper returns review JSON;
- import works without the optional MCP package;
- server startup reports the missing optional MCP package clearly when it is not installed.

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
- MCP adapter import/server availability check
