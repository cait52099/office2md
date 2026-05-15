# office2md v0.4.0-rc1 Release Notes

Status: release candidate for v0.4.0 P1.

## Scope

v0.4.0-rc1 adds the conservative Workspace Manifest / Version Foundation MVP.

This checkpoint does not add Wiki editing, AI suggestions, automatic migration, deletion behavior, Marker integration, AI, OCR, embeddings, vector search, cloud features, conversion changes, runner process-control changes, build-library changes, search/ranking changes, Graph View changes, or Obsidian export changes.

## Command

```powershell
python -m office2md.cli workspace-init WORKSPACE_PATH
```

Options:

- `--dry-run`
- `--overwrite-manifests`

## Workspace Skeleton

`workspace-init` creates missing workspace folders:

```text
conversion/
library/
wiki/
wiki/Concepts/
wiki/Notes/
wiki/Corrections/
wiki/_suggestions/
outputs/
outputs/obsidian/
outputs/reports/
outputs/html/
outputs/_manifests/
logs/
versions/
```

These folders provide the initial RAM / Wiki / Output / Version foundation without requiring Git or changing existing document-processing workflows.

## Manifests

`workspace_manifest.json`

- `schema_version`
- `office2md_version`
- `workspace_path`
- `created_at`
- `updated_at`
- `layers`
- `folders`

`source_manifest.json`

- `schema_version`
- `source_roots`
- `sources`
- `generated_at`

`versions/library_versions.json`

- `schema_version`
- `library_versions`

`versions/output_versions.json`

- `schema_version`
- `output_versions`

## Safety Behavior

- Running `workspace-init` repeatedly is safe.
- Existing files are not deleted.
- `workspace_manifest.json` refreshes `updated_at`.
- Existing `source_manifest.json`, `library_versions.json`, and `output_versions.json` are preserved by default.
- `--overwrite-manifests` explicitly replaces the preserved source/version manifests.
- `--dry-run` prints planned directories and manifest files without writing anything.

## Helpers

The release also adds library-safe helpers:

- `detect_workspace(path)`
- `summarize_workspace(path)`

## Validation

- `python -m pytest`
- `python -m ruff check .`
- CLI help checks:
  - `workspace-init`
  - `export-obsidian`
  - `convert`
  - `build-library`
  - `search-library`
  - `locate-document`
  - `library-report`
- temp workspace smoke
- dry-run smoke
