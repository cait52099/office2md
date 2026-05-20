# office2md v0.4.0-rc3 Release Notes

Status: release candidate for v0.4.0 P3.

## Scope

v0.4.0-rc3 adds manual Library Version Registration for office2md workspaces.

This checkpoint does not change build-library internals, conversion behavior, runner process-control behavior, search/ranking behavior, Graph View behavior, Obsidian export behavior, Wiki editing, AI suggestions, Marker integration, AI, OCR, embeddings, vector search, or cloud features.

## Command

```powershell
python -m office2md.cli workspace-register-library WORKSPACE_PATH LIBRARY_PATH
```

Options:

- `--dry-run`
- `--label`
- `--notes`
- `--allow-dirty-source`
- `--library-version-id`

## Library Version Registration

`workspace-register-library` validates that `WORKSPACE_PATH` is an office2md workspace and that `LIBRARY_PATH` is either a built library folder or a direct `library.db` path.

The command appends a record to:

```text
versions/library_versions.json
```

It does not build a library, run conversion, modify source files, or remove previous version records.

## Version Record

Each version record includes:

- `library_version_id`
- `registered_at`
- `office2md_version`
- `workspace_path`
- `library_path`
- `label`
- `notes`
- `source_manifest_hash`
- `source_counts`
- `source_dirty`
- `library_files`
- `library_metrics`
- `warnings`

## Hashes and Metrics

- `source_manifest_hash` hashes the current `source_manifest.json`.
- `library.db` SHA-256 is recorded when present.
- `library_index.json` SHA-256 is recorded when present.
- `library_graph.json` SHA-256 is recorded when present.
- Library metrics are gathered through the existing `library_report()` helper.

Recorded library metrics include document, chunk, entity, chunks-without-locator, noisy chunk, low-quality document, and page-level PDF document counts where available.

## Dirty Source Warnings

If `source_manifest.json` reports changed or missing sources:

- warnings are printed by the CLI;
- warnings are recorded in the version record;
- source files are not modified;
- registration remains append-only.

## Dry-Run Behavior

`--dry-run` builds the planned version record and prints that `versions/library_versions.json` was not written. Existing version history remains unchanged.

## Validation

- `python -m pytest`
- `python -m ruff check .`
- CLI help checks:
  - `workspace-init`
  - `workspace-scan`
  - `workspace-register-library`
  - `export-obsidian`
  - `convert`
  - `build-library`
  - `search-library`
  - `locate-document`
  - `library-report`
- temp workspace/source/library smoke
- second registration append smoke
- dry-run no-write smoke
