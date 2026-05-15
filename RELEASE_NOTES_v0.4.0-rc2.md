# office2md v0.4.0-rc2 Release Notes

Status: release candidate for v0.4.0 P2.

## Scope

v0.4.0-rc2 adds conservative source manifest population for the workspace foundation introduced in rc1.

This checkpoint does not add Wiki editing, AI suggestions, Marker integration, AI, OCR, embeddings, vector search, cloud features, conversion changes, runner process-control changes, build-library changes, search/ranking changes, Graph View changes, or Obsidian export changes.

## Command

```powershell
python -m office2md.cli workspace-scan WORKSPACE_PATH SOURCE_PATH
```

Options:

- `--dry-run`
- `--include-hidden`
- `--hash / --no-hash`
- `--max-files`
- `--relative-paths / --absolute-paths`

## Source Manifest Population

`workspace-scan` validates that `WORKSPACE_PATH` is an office2md workspace, registers `SOURCE_PATH` in `source_roots`, and updates `source_manifest.json` with supported source files and their traceability metadata.

Each source record includes:

- stable `source_id`
- `source_root`
- `absolute_path`
- `relative_path`
- `file_name`
- `extension`
- `size_bytes`
- `modified_time`
- `sha256`
- `status`
- `previous_status`
- `changed`
- `scanned_at`

The manifest includes:

- `schema_version`
- `generated_at`
- `source_roots`
- `sources`
- `counts`
- `last_scan`

Counts include:

- `total_sources`
- `active_sources`
- `new_sources`
- `changed_sources`
- `missing_sources`

## Tracking Behavior

- First discovery is recorded as `new`.
- Unchanged files become `active` on later scans.
- Modified size, modified time, or checksum is recorded as `changed`.
- Missing historical files are preserved and marked `missing` instead of being deleted.
- `--max-files` records a limited scan and does not mark unscanned historical records as missing.
- Dot-prefixed hidden paths are excluded by default; `--include-hidden` includes hidden paths supported by the existing scanner flow where feasible.

## Safety Behavior

- `workspace-scan` only updates `source_manifest.json`.
- It does not run conversion.
- It does not run `build-library`.
- It does not create Knowledge Packs.
- It does not modify source files.
- `--dry-run` computes planned counts and prints that `source_manifest.json` was not written.

## Validation

- `python -m pytest`
- `python -m ruff check .`
- CLI help checks:
  - `workspace-init`
  - `workspace-scan`
  - `export-obsidian`
  - `convert`
  - `build-library`
  - `search-library`
  - `locate-document`
  - `library-report`
- temp workspace/source smoke
- changed-file smoke
- missing-file smoke
- dry-run smoke
