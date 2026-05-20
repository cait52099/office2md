# office2md v0.4.0 Release Notes

Status: final v0.4.0 release.

## Scope

v0.4.0 adds the local workspace traceability foundation for office2md:

```text
workspace-init -> workspace-scan -> workspace-register-library -> workspace-register-output -> workspace-status
```

This release establishes RAM / Wiki / Output / Version workspace folders and manifest-based lineage from source files to built libraries to generated outputs.

This release does not add a dedicated trace command, implement Wiki editing, implement AI suggestions, add a GUI workspace dashboard, add Marker integration, add AI/OCR/embedding/vector/cloud work, or change conversion, runner, build-library, search/ranking, Graph View, or Obsidian export behavior.

## Workspace Foundation

`workspace-init` creates the conservative workspace skeleton:

- `conversion/`
- `library/`
- `wiki/`
- `wiki/Concepts/`
- `wiki/Notes/`
- `wiki/Corrections/`
- `wiki/_suggestions/`
- `outputs/`
- `outputs/obsidian/`
- `outputs/reports/`
- `outputs/html/`
- `outputs/_manifests/`
- `logs/`
- `versions/`

It creates:

- `workspace_manifest.json`
- `source_manifest.json`
- `versions/library_versions.json`
- `versions/output_versions.json`

The command is idempotent, supports `--dry-run`, and preserves source/version manifests unless `--overwrite-manifests` is explicitly used.

## Source Manifest Tracking

`workspace-scan` registers source roots and source file metadata in `source_manifest.json`.

It records:

- stable source IDs;
- absolute and relative paths;
- file names and extensions;
- size and modified time;
- SHA-256 checksums when enabled;
- source status such as `new`, `active`, `changed`, and `missing`.

It preserves historical records, marks missing files instead of removing them, supports `--dry-run`, excludes hidden paths by default, and avoids marking unscanned historical records missing during limited `--max-files` scans.

## Library Version Tracking

`workspace-register-library` appends built library records to `versions/library_versions.json`.

Each record includes:

- `library_version_id`
- `source_manifest_hash`
- `source_counts`
- library file hashes for `library.db`, `library_index.json`, and `library_graph.json` when present;
- library metrics from the existing `library_report()` helper;
- dirty source warnings when changed or missing sources are present.

The command is manual and append-only. It does not run conversion, build a library, modify source files, or remove version history.

## Output Version Tracking

`workspace-register-output` appends generated output records to `versions/output_versions.json`.

Each record includes:

- `output_version_id`
- linked `library_version_id`
- `source_manifest_hash`
- output type;
- file hash or stable folder hash;
- file count and total size;
- recognized output files;
- parsed Obsidian export manifest summary when present.

Obsidian vault folders are detected from `00_Index.md` and `_office2md/export_manifest.json`. The command does not generate exports, call `export-obsidian`, modify output files, or remove output history.

## Read-Only Workspace Status

`workspace-status` provides a read-only traceability summary.

It reads:

- `workspace_manifest.json`
- `source_manifest.json`
- `versions/library_versions.json`
- `versions/output_versions.json`

It summarizes:

- workspace status;
- source manifest counts;
- latest library version;
- latest output version;
- warnings and errors;
- the latest traceability chain:

```text
source_manifest_hash -> library_version_id -> output_version_id
```

`--json` prints parseable JSON only. `--show-history` and `--limit` show recent version history. `--strict` returns non-zero for missing required manifests or broken linkage while allowing normal warnings to remain informational.

## Documentation

Updated documentation includes:

- `README.md`
- `docs/usage/workspace.md`
- `docs/design/v040_workspace_layering_ram_wiki_output.md`
- `RELEASE_CHECKLIST.md`

## Validation

Final release validation includes:

- `python -m pytest`
- `python -m ruff check .`
- `python -m compileall office2md/gui`
- CLI help checks for workspace, export, conversion, library, search, locate, and report commands;
- full tiny workspace traceability smoke;
- workspace dry-run smoke;
- local CML125 search/export dry-run smoke when the CML125 library is available.
