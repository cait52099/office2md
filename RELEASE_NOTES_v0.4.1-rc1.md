# office2md v0.4.1-rc1 Release Notes

Status: release candidate for v0.4.1 P1.

## Scope

v0.4.1-rc1 adds a read-only GUI Workspace Dashboard.

This checkpoint does not modify workspace files, create or update manifests, run `workspace-init`, run `workspace-scan`, run conversion, run `build-library`, run `export-obsidian`, change conversion behavior, change runner behavior, change build-library internals, change search/ranking behavior, change Graph View behavior, change Obsidian export behavior, implement Wiki editing, implement AI suggestions, add Marker integration, or add AI, OCR, embedding, vector, or cloud work.

## GUI Workspace Page

The Streamlit sidebar now includes:

```text
Workspace
```

Inputs:

- `Workspace Path`
- `Show history`
- `History limit`

The page reuses the existing workspace status summary logic through `summarize_workspace_status()` via GUI helper functions. It does not shell out or duplicate workspace status implementation.

## Dashboard Sections

The page displays:

- workspace detected / not detected state;
- workspace path;
- created and updated timestamps;
- missing folders and missing manifests;
- source manifest counts and last scan details;
- changed or missing source warnings;
- total library versions and latest library version details;
- library metrics including documents, chunks, entities, and chunks without locator;
- total output versions and latest output version details;
- Obsidian export manifest summary when present;
- warning and error messages;
- traceability chain:

```text
source_manifest_hash -> library_version_id -> output_version_id
```

When `Show history` is enabled, recent library and output versions are displayed up to `History limit`.

## JSON Download

The page includes:

```text
Download workspace status JSON
```

The download payload is generated from the same status summary data shown on the page and is parseable JSON.

## Read-Only Behavior

The GUI Workspace page is read-only:

- no subprocess;
- no automatic workspace initialization;
- no automatic source scan;
- no conversion;
- no build-library;
- no export;
- no manifest writes;
- no source or output file modifications.

## Validation

- `python -m pytest`
- `python -m ruff check .`
- `python -m compileall office2md/gui`
- CLI help checks:
  - `workspace-status`
  - `workspace-init`
  - `workspace-scan`
  - `workspace-register-library`
  - `workspace-register-output`
  - `export-obsidian`
  - `convert`
  - `build-library`
  - `search-library`
  - `locate-document`
  - `library-report`
- temp init-only workspace GUI helper smoke
- full traceability workspace GUI helper smoke
