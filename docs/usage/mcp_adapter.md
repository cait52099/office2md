# office2md MCP Adapter

The office2md MCP adapter exposes the Agent Gateway as read-only tools for AI clients.

Available tools:

- `kb_list`
- `kb_context`
- `kb_review`

The adapter wraps the same helpers used by:

```powershell
python -m office2md.cli kb-list
python -m office2md.cli kb-context
python -m office2md.cli kb-review
```

## Run

The wrapper functions are available without MCP installed. To run as an MCP server, install an MCP runtime package in the environment, then run:

```powershell
python -m office2md.mcp_adapter
```

## kb_list

Lists registered libraries from a catalog:

```json
{
  "catalog_path": "C:/path/to/libraries.json"
}
```

Returns schema `office2md.library_catalog.v1`.

## kb_context

Builds one evidence-first agent context packet:

```json
{
  "catalog_path": "C:/path/to/libraries.json",
  "query": "vacuum pump fault",
  "libraries": "lib-a,lib-b",
  "limit": 5,
  "context": 1
}
```

Returns schema `office2md.agent_context.v1`.

Evidence includes per-library provenance where available:

- `library_id`
- `library_name`
- `library_path`
- `source_file`
- `locator`
- `chunk_id`
- `document_id`

If a library is stale or unknown, the response includes warnings and `next_steps`. The adapter does not auto-update.

## kb_review

Reviews update readiness for one registered library:

```json
{
  "catalog_path": "C:/path/to/libraries.json",
  "library_id": "lib-a"
}
```

Returns schema `office2md.kb_review.v1`.

This is review-only. It does not execute update-library.

## Safety

The adapter does not:

- expose unrestricted SQL;
- execute shell commands;
- modify source files;
- modify conversion output;
- modify library DB, index, graph, or evidence;
- modify registry, state, change plan, or update result files;
- auto-update stale libraries;
- delete evidence;
- run watchers or background processes.

OfficeCLI remains `diagnostic_only`.
