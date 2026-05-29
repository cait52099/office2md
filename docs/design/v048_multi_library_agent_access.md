# v0.4.8 Multi-library Agent Access and Update Review Foundation

## Purpose

v0.4.8 prepares office2md for agent workflows that need to choose between multiple local Knowledge Libraries.

The release keeps existing single-library commands unchanged and adds an additive catalog layer for routing and provenance. It also improves `update-library` dry-run/review output so humans and agents can decide whether a library is current, stale, or too large to update in one pass.

## Update Review Foundation

`update-library` now includes additive review fields in its result:

- `review_summary`;
- `large_folder_warnings`;
- `next_steps`;
- optional Markdown review report via `--review-report`.

The review summary records:

- status: `current`, `stale`, or `unknown`;
- total source count;
- pending change count;
- planned conversion count;
- planned reuse count;
- deleted/missing, stale, unsupported, and moved/renamed candidate counts;
- large-folder and high-pending-change flags;
- human-readable guidance.

These fields do not change update execution. `update-library` still converts only `new` and `modified` files, reuses unchanged valid Knowledge Packs, records deleted/missing/stale sources without deleting evidence, and rebuilds via existing `build_library()`.

## Library Catalog

Schema:

```text
office2md.library_catalog.v1
```

A catalog record contains:

- `library_id`;
- `library_name`;
- `library_path`;
- `source_root`;
- `registered_at`;
- metadata documenting required agent evidence fields.

Example:

```json
{
  "library_id": "cml125",
  "library_name": "CML125 Technical Library",
  "library_path": "D:/libraries/cml125",
  "source_root": "D:/source/cml125"
}
```

## Agent Evidence Contract

When an answer draws from any library, evidence must carry:

- `library_id`;
- `library_name`;
- `library_path`;
- `source_file`;
- `locator`;
- `chunk_id`;
- `document_id`.

The catalog does not merge or rewrite existing library evidence. It lets agents route to one or more libraries and preserve provenance.

## Future Multi-library Access

Future commands may add:

- multi-library search;
- multi-library report context;
- cross-library library-status summaries;
- read-only MCP tools that wrap these CLI/core contracts.

Future MCP must not expose unrestricted SQL, shell execution, write-back, or direct file mutation.

## Non-Goals

v0.4.8 does not include:

- multi-library search execution;
- MCP implementation;
- embeddings or vector search;
- OCR;
- Obsidian plugin;
- write-back;
- unrestricted SQL;
- shell execution;
- conversion behavior changes;
- build-library behavior changes;
- search ranking, aliases, or token fallback changes;
- update-library execution semantic changes;
- watcher/background update;
- automatic deletion.

OfficeCLI remains `diagnostic_only`.
