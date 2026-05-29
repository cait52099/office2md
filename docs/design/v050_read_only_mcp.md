# v0.5.0 Read-Only MCP Adapter Design

## Purpose

v0.5.0 adds a small MCP adapter over the existing office2md Agent Gateway so AI tools can request library lists, evidence context, and update-readiness review without manually chaining CLI commands.

The MCP adapter is intentionally read-only. It wraps existing gateway helpers and does not introduce new search, update, conversion, or SQL paths.

## Exposed Tools

The adapter exposes only:

- `kb_list`
- `kb_context`
- `kb_review`

These map directly to:

- `office2md.kb_gateway.kb_list`
- `office2md.kb_gateway.kb_context`
- `office2md.kb_gateway.kb_review`

## Tool Contracts

### kb_list

Input:

- `catalog_path`

Output:

- library catalog JSON using schema `office2md.library_catalog.v1`.

### kb_context

Input:

- `catalog_path`
- `query`
- one of `library_id`, `library_ids`, or `libraries`
- `limit`
- `context`

Output:

- agent context JSON using schema `office2md.agent_context.v1`.

Evidence preserves where available:

- `library_id`
- `library_name`
- `library_path`
- `source_file`
- `locator`
- `chunk_id`
- `document_id`
- `document_title`
- `document_kind`
- `evidence_type`
- `confidence`
- `limitation`

### kb_review

Input:

- `catalog_path`
- `library_id`

Output:

- read-only review payload using schema `office2md.kb_review.v1`.

`kb_review` remains dry-run/review only. It does not execute update-library.

## Safety Model

The adapter must not:

- expose unrestricted SQL;
- execute shell commands;
- modify source files;
- modify conversion output;
- modify library DB, index, graph, or evidence;
- modify source registry, library state, change plan, or update result files;
- auto-update stale libraries;
- delete evidence;
- start a watcher or background process.

Stale or unknown libraries are returned as warnings and `next_steps`.

## Optional Dependency

The Python wrapper functions are importable without the MCP package. Running an MCP server requires the optional `mcp` package. This keeps office2md usable without MCP installed.

## Non-Goals

v0.5.0 does not include:

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
