# office2md Release Readiness Checklist

v0.4.1-rc2 GUI Workspace path guidance checkpoint evidence:

- [x] `python -m pytest` reports 141 passed.
- [x] `python -m ruff check .` reports all checks passed.
- [x] `python -m compileall office2md/gui` succeeds.
- [x] Workspace page input label is `Workspace Root Path`.
- [x] Helper text explains that the path must be created by `workspace-init`.
- [x] Helper text explains that Workspace Root Path is separate from Library Path.
- [x] Helper text explains that conversion output folders, built library folders, and Obsidian export folders are not workspace roots.
- [x] Workspace-not-detected guidance shows expected markers: `workspace_manifest.json`, `source_manifest.json`, `versions/library_versions.json`, and `versions/output_versions.json`.
- [x] Path type hints identify built library folders.
- [x] Path type hints identify Obsidian export folders.
- [x] Path type hints identify conversion / Knowledge Pack-like folders.
- [x] Path type hints identify `*-office2md-output` output folders.
- [x] Non-workspace paths show a `workspace-init` command hint.
- [x] `interview-office2md-output` suggests `interview.office2md`.
- [x] Valid init-only workspaces are treated as valid and show `Workspace detected`.
- [x] Init-only workspaces can show zero source/library/output counts without error.
- [x] Init-only guidance explains that scan/register history is empty.
- [x] Init-only guidance shows next-step command hints for `workspace-scan`, `workspace-register-library`, and `workspace-register-output`.
- [x] Current full valid workspace behavior is unchanged.
- [x] The page is read-only: no subprocess, no automatic workspace-init, no automatic workspace-scan, no conversion, no build-library, no export, and no file writes.
- [x] GUI/helper smoke confirms `C:\Users\hcai\Downloads\interview-office2md-output` is classified as output-like and receives a workspace-init hint.
- [x] GUI/helper smoke confirms `C:\Users\hcai\Downloads\interview.office2md` is detected as a valid init-only workspace and receives next-step hints.
- [x] Conversion behavior is unchanged.
- [x] Runner process-control behavior is unchanged.
- [x] Build-library internals are unchanged.
- [x] Search/ranking/aliases/token fallback behavior is unchanged.
- [x] Graph View behavior is unchanged.
- [x] Obsidian export behavior is unchanged.
- [x] No Wiki editing workflow is included.
- [x] No AI suggestions are included.
- [x] No Marker, AI, OCR, embedding, vector, or cloud work is included.

v0.4.1-rc1 GUI Workspace Dashboard checkpoint evidence:

- [x] `python -m pytest` reports 137 passed.
- [x] `python -m ruff check .` reports all checks passed.
- [x] `python -m compileall office2md/gui` succeeds.
- [x] GUI sidebar includes `Workspace`.
- [x] Workspace page includes `Workspace Path`.
- [x] Workspace page includes `Show history`.
- [x] Workspace page includes `History limit`.
- [x] Workspace page reuses existing `summarize_workspace_status()` through GUI helpers.
- [x] Workspace page shows workspace detected / not detected status.
- [x] Workspace page shows workspace path, created time, updated time, missing folders, and missing manifests.
- [x] Source section shows total, active, new, changed, and missing source counts.
- [x] Source section shows source root count, last scan, and changed/missing source warnings.
- [x] Library Versions section shows total library versions and latest library version details.
- [x] Library Versions section shows latest library version ID, registration time, label, source manifest hash, documents, chunks, entities, chunks without locator, and warnings.
- [x] Output Versions section shows total output versions and latest output version details.
- [x] Output Versions section shows latest output version ID, registration time, output type, label, linked library version ID, source manifest hash, file count, total size, export manifest summary, and warnings.
- [x] Traceability section shows `source_manifest_hash -> library_version_id -> output_version_id`.
- [x] `Show history` displays recent library and output versions.
- [x] `History limit` is respected by the reused status helper.
- [x] `Download workspace status JSON` is present.
- [x] JSON download payload is parseable and generated from the same status summary data.
- [x] Invalid workspace paths are handled with not-detected/error messages.
- [x] Missing manifests, broken output/library linkage, and source hash mismatch warnings are surfaced from the status summary.
- [x] GUI helper smoke loads an init-only workspace and parses JSON.
- [x] GUI helper smoke loads full source/library/output/traceability summary.
- [x] Existing CLI workspace-status tests still pass.
- [x] The page is read-only: no subprocess, no automatic workspace-init, no automatic workspace-scan, no conversion, no build-library, no export, and no file writes.
- [x] Conversion behavior is unchanged.
- [x] Runner process-control behavior is unchanged.
- [x] Build-library internals are unchanged.
- [x] Search/ranking/aliases/token fallback behavior is unchanged.
- [x] Graph View behavior is unchanged.
- [x] Obsidian export behavior is unchanged.
- [x] No Wiki editing workflow is included.
- [x] No AI suggestions are included.
- [x] No Marker, AI, OCR, embedding, vector, or cloud work is included.

v0.4.0 final release evidence:

- [x] `python -m pytest` reports 134 passed.
- [x] `python -m ruff check .` reports all checks passed.
- [x] `python -m compileall office2md/gui` succeeds.
- [x] `pyproject.toml` version is updated to `0.4.0`.
- [x] `office2md/__init__.py` version is updated to `0.4.0`.
- [x] `workspace-init` exists and creates the RAM / Wiki / Output / Version folder foundation.
- [x] `workspace-init` creates `workspace_manifest.json`.
- [x] `workspace-init` creates `source_manifest.json`.
- [x] `workspace-init` creates `versions/library_versions.json`.
- [x] `workspace-init` creates `versions/output_versions.json`.
- [x] `workspace-init --dry-run` writes nothing.
- [x] `workspace-init` is idempotent and preserves existing source/version manifests by default.
- [x] `workspace-scan` exists and records source roots.
- [x] `workspace-scan` records file metadata and SHA-256 checksums when enabled.
- [x] `workspace-scan` detects new, active, changed, and missing files.
- [x] `workspace-scan --dry-run` writes nothing.
- [x] `workspace-scan --max-files` does not falsely mark unscanned historical files missing.
- [x] `workspace-register-library` exists and appends to `versions/library_versions.json`.
- [x] Library version records include `source_manifest_hash`, source counts, library file hashes, and library metrics from existing `library_report()` behavior.
- [x] Dirty source warnings are recorded for changed or missing sources.
- [x] `workspace-register-library --dry-run` writes nothing.
- [x] `workspace-register-library` does not run build-library.
- [x] `workspace-register-output` exists and appends to `versions/output_versions.json`.
- [x] Output version records include `library_version_id`, `source_manifest_hash`, output file/folder hashes, and output summary.
- [x] Obsidian vault output is detected and Obsidian export manifests are parsed when present.
- [x] `workspace-register-output --dry-run` writes nothing.
- [x] `workspace-register-output` does not run export-obsidian.
- [x] `workspace-status` exists and is read-only.
- [x] `workspace-status --json` outputs parseable JSON only.
- [x] `workspace-status --show-history` and `--limit` work.
- [x] `workspace-status --strict` fails for missing required manifests or broken linkage and does not fail normal warnings.
- [x] `workspace-status` shows source, library, output summaries and the traceability chain `source_manifest_hash -> library_version_id -> output_version_id`.
- [x] CLI help checks pass for `workspace-init`, `workspace-scan`, `workspace-register-library`, `workspace-register-output`, `workspace-status`, `export-obsidian`, `convert`, `build-library`, `search-library`, `locate-document`, and `library-report`.
- [x] Full tiny traceability smoke passes.
- [x] Dry-run smoke passes for workspace init, scan, library registration, and output registration.
- [x] Local CML125 smoke is skipped when no CML125 library is found.
- [x] README, workspace usage docs, workspace layering design docs, release checklist, and final release notes are updated.
- [x] No dedicated workspace-trace command is included.
- [x] No Wiki editing workflow is included.
- [x] No AI suggestions are included.
- [x] No GUI workspace dashboard is included.
- [x] No Marker integration is included.
- [x] No AI, OCR, embedding, vector, or cloud work is included.
- [x] Conversion behavior is unchanged.
- [x] Runner process-control behavior is unchanged.
- [x] Build-library internals are unchanged.
- [x] Search/ranking/aliases/token fallback behavior is unchanged.
- [x] Graph View behavior is unchanged.
- [x] Obsidian export behavior is unchanged.

v0.4.0-rc5 Workspace Status checkpoint evidence:

- [x] `python -m pytest` reports 134 passed.
- [x] `python -m ruff check .` reports all checks passed.
- [x] `python -m office2md.cli workspace-status --help` shows the new command.
- [x] `workspace-status` accepts `WORKSPACE_PATH`.
- [x] `workspace-status` supports `--json`.
- [x] `workspace-status` supports `--show-history`.
- [x] `workspace-status` supports `--limit`.
- [x] `workspace-status` supports `--strict`.
- [x] The command validates that `WORKSPACE_PATH` is an office2md workspace.
- [x] The command reads `workspace_manifest.json`, `source_manifest.json`, `versions/library_versions.json`, and `versions/output_versions.json`.
- [x] The command does not write files or modify manifests.
- [x] The command does not run scan, conversion, build-library, or export-obsidian.
- [x] The command does not modify source files or output files.
- [x] Readable output includes workspace status, source manifest summary, library version summary, output version summary, latest traceability chain, warnings, and errors.
- [x] JSON output includes `workspace`, `source_manifest`, `library_versions`, `output_versions`, `traceability`, `warnings`, and `errors`.
- [x] `--json` prints parseable JSON only with no table text before or after the JSON payload.
- [x] The latest traceability chain is shown as `source_manifest_hash -> library_version_id -> output_version_id`.
- [x] Warning behavior covers current source hash differing from latest library version hash.
- [x] Warning behavior covers current source hash differing from latest output version hash.
- [x] Warning behavior covers latest output linking to a missing `library_version_id`.
- [x] Normal warnings do not fail the command.
- [x] Missing required manifests or broken linkage return non-zero under `--strict`.
- [x] `--show-history` shows recent library versions and output versions.
- [x] `--limit` limits history output.
- [x] Temp workspace smoke confirms readable summary and parseable JSON.
- [x] Full source/library/output smoke confirms summaries and latest traceability chain.
- [x] History smoke confirms `--show-history --limit 1` is limited.
- [x] Conversion behavior is unchanged.
- [x] Runner process-control behavior is unchanged.
- [x] Build-library internals are unchanged.
- [x] Search/ranking/aliases/token fallback behavior is unchanged.
- [x] Graph View behavior is unchanged.
- [x] Obsidian export behavior is unchanged.
- [x] No Wiki editing workflow is included.
- [x] No AI suggestions are included.
- [x] No Marker, AI, OCR, embedding, vector, or cloud work is included.

v0.4.0-rc4 Output Version Registration checkpoint evidence:

- [x] `python -m pytest` reports 123 passed.
- [x] `python -m ruff check .` reports all checks passed.
- [x] `python -m office2md.cli workspace-register-output --help` shows the new command.
- [x] `workspace-register-output` accepts `WORKSPACE_PATH` and `OUTPUT_PATH`.
- [x] `workspace-register-output` supports `--dry-run`.
- [x] `workspace-register-output` supports `--label`.
- [x] `workspace-register-output` supports `--notes`.
- [x] `workspace-register-output` supports `--output-type`.
- [x] `workspace-register-output` supports `--library-version-id`.
- [x] `workspace-register-output` supports `--output-version-id`.
- [x] `workspace-register-output` supports `--allow-missing-library-version`.
- [x] The command validates that `WORKSPACE_PATH` is an office2md workspace.
- [x] The command validates that `OUTPUT_PATH` exists as a file or folder.
- [x] The command appends records to `versions/output_versions.json`.
- [x] Previous output version records are preserved.
- [x] Output version records include ID, registration time, office2md version, workspace path, output path, output type, label, notes, library version ID, source manifest hash, source counts, output file summary, export manifest summary, and warnings.
- [x] File outputs record SHA-256, `file_count = 1`, and total size.
- [x] Folder outputs record recursive file count, total size, and stable folder SHA-256.
- [x] Folder SHA-256 uses sorted relative paths plus each file hash.
- [x] Recognized files are recorded for known output layouts.
- [x] Obsidian vaults are detected from `00_Index.md` and `_office2md/export_manifest.json`.
- [x] Obsidian export manifests are parsed when present.
- [x] Export type, exported document count, exported concept count, and export warnings are recorded when available.
- [x] Explicit `--library-version-id` links to that library version.
- [x] A single library version is linked automatically.
- [x] Multiple library versions use the latest `registered_at` and record a warning.
- [x] Missing library version blocks by default.
- [x] `--allow-missing-library-version` allows registration with a warning and no library/source linkage.
- [x] `--dry-run` builds a planned output version record and writes nothing.
- [x] `--dry-run` prints that `versions/output_versions.json` was not written.
- [x] Temp workspace/source/library/Obsidian smoke registers one output version with output type, library linkage, source hash, folder hash, and export manifest summary.
- [x] Second output registration smoke preserves the first output version and appends a new version.
- [x] Dry-run smoke confirms `versions/output_versions.json` content is unchanged.
- [x] Conversion behavior is unchanged.
- [x] Runner process-control behavior is unchanged.
- [x] Build-library internals are unchanged.
- [x] Search/ranking/aliases/token fallback behavior is unchanged.
- [x] Graph View behavior is unchanged.
- [x] Obsidian export behavior is unchanged.
- [x] No Wiki editing workflow is included.
- [x] No AI suggestions are included.
- [x] No Marker, AI, OCR, embedding, vector, or cloud work is included.

v0.4.0-rc3 Library Version Registration checkpoint evidence:

- [x] `python -m pytest` reports 112 passed.
- [x] `python -m ruff check .` reports all checks passed.
- [x] `python -m office2md.cli workspace-register-library --help` shows the new command.
- [x] `workspace-register-library` accepts `WORKSPACE_PATH` and `LIBRARY_PATH`.
- [x] `workspace-register-library` supports `--dry-run`.
- [x] `workspace-register-library` supports `--label`.
- [x] `workspace-register-library` supports `--notes`.
- [x] `workspace-register-library` supports `--allow-dirty-source`.
- [x] `workspace-register-library` supports `--library-version-id`.
- [x] The command validates that `WORKSPACE_PATH` is an office2md workspace.
- [x] The command validates that `LIBRARY_PATH` is a built library folder or `library.db` path.
- [x] The command appends records to `versions/library_versions.json`.
- [x] Previous library version records are preserved.
- [x] Version records include ID, registration time, office2md version, workspace path, library path, label, notes, source manifest hash, source counts, source dirty flag, library files, library metrics, and warnings.
- [x] `source_manifest_hash` hashes the current `source_manifest.json`.
- [x] `library.db` SHA-256 is recorded when present.
- [x] `library_index.json` SHA-256 is recorded when present.
- [x] `library_graph.json` SHA-256 is recorded when present.
- [x] Library metrics come from existing `library_report()` behavior.
- [x] Source counts are recorded with total, active, new, changed, and missing source counts.
- [x] Changed and missing sources generate dirty source warnings.
- [x] Dirty source warnings are printed by the CLI.
- [x] Dirty source warnings are recorded in the version record.
- [x] `--dry-run` builds a planned version record and writes nothing.
- [x] `--dry-run` prints that `versions/library_versions.json` was not written.
- [x] Temp workspace/source/library smoke registers one version with source hash, metrics, and library DB hash.
- [x] Second registration smoke preserves the first version and appends a new version.
- [x] Dry-run smoke confirms `versions/library_versions.json` content is unchanged.
- [x] Conversion behavior is unchanged.
- [x] Runner process-control behavior is unchanged.
- [x] Build-library internals are unchanged.
- [x] Search/ranking/aliases/token fallback behavior is unchanged.
- [x] Graph View behavior is unchanged.
- [x] Obsidian export behavior is unchanged.
- [x] No Wiki editing workflow is included.
- [x] No AI suggestions are included.
- [x] No Marker, AI, OCR, embedding, vector, or cloud work is included.

v0.4.0-rc2 workspace-scan / source manifest population checkpoint evidence:

- [x] `python -m pytest` reports 105 passed.
- [x] `python -m ruff check .` reports all checks passed.
- [x] `python -m office2md.cli workspace-scan --help` shows the new command.
- [x] `workspace-scan` accepts `WORKSPACE_PATH` and `SOURCE_PATH`.
- [x] `workspace-scan` supports `--dry-run`.
- [x] `workspace-scan` supports `--include-hidden`.
- [x] `workspace-scan` supports `--hash / --no-hash`.
- [x] `workspace-scan` supports `--max-files`.
- [x] `workspace-scan` supports `--relative-paths / --absolute-paths`.
- [x] `workspace-scan` validates that `WORKSPACE_PATH` is an office2md workspace and recommends `workspace-init` when it is not.
- [x] `workspace-scan` only updates `source_manifest.json`.
- [x] `workspace-scan` does not run conversion, run `build-library`, create Knowledge Packs, or modify source files.
- [x] `source_manifest.json` includes `schema_version`, `generated_at`, `source_roots`, `sources`, `counts`, and `last_scan`.
- [x] Source manifest counts include `total_sources`, `active_sources`, `new_sources`, `changed_sources`, and `missing_sources`.
- [x] Source records include stable ID, root, absolute path, relative path, file name, extension, size, modified time, checksum, status, previous status, changed flag, and scan time.
- [x] First discovery is recorded as `new`.
- [x] Unchanged second scan becomes `active`.
- [x] Modified size, modified time, or checksum becomes `changed`.
- [x] Missing historical files are preserved and marked `missing`.
- [x] `--max-files` records a limited scan without marking unscanned historical records as missing.
- [x] `--dry-run` computes planned counts, writes nothing, and prints that `source_manifest.json` was not written.
- [x] Dot-prefixed hidden paths are excluded by default.
- [x] `--include-hidden` includes hidden paths supported by the scanner flow where feasible.
- [x] Temp source smoke records two sources and two SHA-256 values.
- [x] Changed-file smoke records `changed_sources = 1`.
- [x] Missing-file smoke preserves the old record with `status = missing`.
- [x] Dry-run smoke confirms `source_manifest.json` content is unchanged.
- [x] Conversion behavior is unchanged.
- [x] Runner process-control behavior is unchanged.
- [x] Build-library internals are unchanged.
- [x] Search/ranking/aliases/token fallback behavior is unchanged.
- [x] Graph View behavior is unchanged.
- [x] Obsidian export behavior is unchanged.
- [x] No Wiki editing workflow is included.
- [x] No AI suggestions are included.
- [x] No Marker, AI, OCR, embedding, vector, or cloud work is included.

v0.4.0-rc1 Workspace Manifest / Version Foundation checkpoint evidence:

- [x] `python -m pytest` reports 98 passed.
- [x] `python -m ruff check .` reports all checks passed.
- [x] `python -m office2md.cli workspace-init --help` shows the new command.
- [x] `workspace-init` accepts `WORKSPACE_PATH`.
- [x] `workspace-init` supports `--dry-run`.
- [x] `workspace-init` supports `--overwrite-manifests`.
- [x] Workspace skeleton creates `conversion/`, `library/`, `wiki/`, `wiki/Concepts/`, `wiki/Notes/`, `wiki/Corrections/`, `wiki/_suggestions/`, `outputs/`, `outputs/obsidian/`, `outputs/reports/`, `outputs/html/`, `outputs/_manifests/`, `logs/`, and `versions/`.
- [x] Workspace foundation represents RAM / Wiki / Output / Version folders without requiring Git.
- [x] `workspace_manifest.json` is created with schema version, office2md version, workspace path, created time, updated time, layers, and folders.
- [x] `source_manifest.json` is created with schema version, source roots, sources, and generated time.
- [x] `versions/library_versions.json` is created with schema version and `library_versions`.
- [x] `versions/output_versions.json` is created with schema version and `output_versions`.
- [x] Second `workspace-init` run succeeds without deleting existing files.
- [x] Second `workspace-init` refreshes `workspace_manifest.json.updated_at`.
- [x] Existing source/version manifests are preserved by default.
- [x] `--overwrite-manifests` explicitly overwrites preserved source/version manifests.
- [x] `--dry-run` prints planned directories and manifest files without writing files.
- [x] `detect_workspace(path)` is added.
- [x] `summarize_workspace(path)` is added.
- [x] Temp workspace smoke confirms all planned folders and manifests exist and a test file under `wiki/Notes/` survives the second run.
- [x] Dry-run smoke confirms no workspace files are written.
- [x] Conversion behavior is unchanged.
- [x] Runner process-control behavior is unchanged.
- [x] Build-library internals are unchanged.
- [x] Search/ranking/aliases/token fallback behavior is unchanged.
- [x] Graph View behavior is unchanged.
- [x] Obsidian export behavior is unchanged.
- [x] No Wiki editing workflow is included.
- [x] No AI suggestions are included.
- [x] No Marker, AI, OCR, embedding, vector, or cloud work is included.

v0.3.2 final release evidence:

- [x] `python -m pytest` reports 91 passed.
- [x] `python -m ruff check .` reports all checks passed.
- [x] `python -m compileall office2md/gui` succeeds.
- [x] CLI `export-obsidian` exists.
- [x] CLI `export-obsidian` supports `--overwrite`.
- [x] CLI `export-obsidian` supports `--dry-run`.
- [x] CLI `export-obsidian` supports `--max-concepts`.
- [x] CLI `export-obsidian` supports `--max-evidence-per-concept`.
- [x] Obsidian vault output structure is documented as `00_Index.md`, `00_Library_Report.md`, `Documents/`, `Concepts/`, and `_office2md/export_manifest.json`.
- [x] Document notes include YAML frontmatter, Related Concepts, and Obsidian `[[wikilinks]]`.
- [x] Concept notes include YAML frontmatter, Related Documents, and Obsidian `[[wikilinks]]`.
- [x] Export manifest records export type, office2md version, paths, counts, warnings, and options.
- [x] Dry-run and overwrite behavior are documented and validated.
- [x] GUI sidebar includes `Export`.
- [x] GUI export page includes `Export to Obsidian Vault`.
- [x] GUI Preview Export uses dry-run behavior.
- [x] GUI Export to Obsidian reuses existing exporter logic directly.
- [x] Obsidian installation is not required to generate the export.
- [x] Assets are intentionally not copied in this MVP and manifests record warnings when assets exist.
- [x] Concept extraction is heuristic/library-native and does not use a fixed equipment vocabulary.
- [x] Tiny fixture export smoke creates the expected vault structure, manifest, document notes, and concept notes.
- [x] Tiny fixture GUI/helper export smoke parses the manifest summary.
- [x] CML125 dry-run export reports 587 planned documents, 20 planned concepts, uncopied asset warning, and creates no full vault.
- [x] CML125 `search-library "vacuum pump fault" --limit 3 --diagnostics-json` uses token fallback and returns useful fault catalog results.
- [x] No Marker integration is included.
- [x] No AI, OCR, embedding, vector, or cloud work is included.
- [x] Conversion behavior is unchanged.
- [x] Runner process-control behavior is unchanged.
- [x] Build-library internals are unchanged.
- [x] Search/ranking/aliases/token fallback behavior is unchanged.
- [x] Graph View behavior is unchanged.
- [x] Library-report scoring is unchanged.

v0.3.2-rc2 GUI Export to Obsidian checkpoint evidence:

- [x] `python -m pytest` reports 91 passed.
- [x] `python -m ruff check .` reports all checks passed.
- [x] `python -m compileall office2md/gui` succeeds.
- [x] Streamlit sidebar includes `Export`.
- [x] Export page includes `Export to Obsidian Vault`.
- [x] Export page includes Current Library Path defaulted from the loaded GUI library path.
- [x] Export page includes Obsidian Vault Output Folder.
- [x] Export page includes Max Concepts.
- [x] Export page includes Max Evidence Per Concept.
- [x] Export page includes Overwrite existing output.
- [x] Export page includes Dry-run.
- [x] Export page includes Preview Export.
- [x] Export page includes Export to Obsidian.
- [x] Preview Export uses dry-run behavior and does not write output files.
- [x] Export to Obsidian calls the existing `office2md.exports.obsidian.export_obsidian()` implementation directly.
- [x] GUI export does not duplicate exporter logic.
- [x] GUI shows output path, counts, warnings, generated structure, and parsed export manifest after real export.
- [x] User-facing text states Obsidian is not required.
- [x] User-facing text states the exported folder can later be opened as an Obsidian vault.
- [x] User-facing text states assets are not copied in this MVP.
- [x] User-facing text states concept quality is heuristic/library-native.
- [x] CLI behavior remains `python -m office2md.cli export-obsidian LIBRARY_PATH VAULT_OUTPUT`.
- [x] Tiny fixture GUI/helper smoke exports a vault and parses `export_manifest.json` with `export_type: obsidian`.
- [x] CML125 helper dry-run records 587 planned documents, 20 planned concepts, uncopied asset warning, and creates no full vault.
- [x] No asset copy support is included.
- [x] No Marker integration is included.
- [x] No PDF/Word/HTML export is included.
- [x] No AI, OCR, embedding, vector, or cloud work is included.
- [x] Conversion behavior is unchanged.
- [x] Runner process-control behavior is unchanged.
- [x] Build-library internals are unchanged.
- [x] Search/ranking/aliases/token fallback behavior is unchanged.
- [x] Graph View behavior is unchanged.
- [x] Library-report scoring is unchanged.
- [x] v0.4 RAM/Wiki/Output layers are not implemented.

v0.3.2-rc1 Obsidian Export CLI MVP checkpoint evidence:

- [x] `python -m pytest` reports 89 passed.
- [x] `python -m ruff check .` reports all checks passed.
- [x] `python -m office2md.cli export-obsidian --help` shows the new command.
- [x] `export-obsidian` accepts `LIBRARY_PATH` and `VAULT_OUTPUT`.
- [x] `export-obsidian` supports `--overwrite`.
- [x] `export-obsidian` supports `--dry-run`.
- [x] `export-obsidian` supports `--max-concepts`.
- [x] `export-obsidian` supports `--max-evidence-per-concept`.
- [x] `LIBRARY_PATH` accepts a built library folder.
- [x] `LIBRARY_PATH` accepts a `library.db` path.
- [x] Non-empty output folders fail unless `--overwrite` is provided.
- [x] `--dry-run` writes no files.
- [x] Vault output creates `00_Index.md`.
- [x] Vault output creates `00_Library_Report.md`.
- [x] Vault output creates `Documents/`.
- [x] Vault output creates `Concepts/`.
- [x] Vault output creates `_office2md/export_manifest.json`.
- [x] Document notes include YAML frontmatter.
- [x] Document notes include Related Concepts.
- [x] Document notes use Obsidian `[[wikilinks]]`.
- [x] Concept notes include YAML frontmatter.
- [x] Concept notes include Related Documents.
- [x] Concept notes use Obsidian `[[wikilinks]]`.
- [x] Export manifest records export type, office2md version, library path, vault output, document count, concept count, warnings, and options.
- [x] Concept extraction uses current-library/library-native concepts from entities, document titles, headings, and chunk text.
- [x] Concept extraction includes noise filtering.
- [x] Concept count is bounded by `--max-concepts`.
- [x] No fixed equipment vocabulary is used.
- [x] Release notes state concept quality is MVP/heuristic and may need real-use tuning.
- [x] Assets are intentionally not copied in the MVP.
- [x] If a source library contains assets, `export_manifest.json` records a warning.
- [x] Tiny fixture smoke converts `tests/fixtures/sample.txt`, builds a library, exports a vault, and parses the manifest.
- [x] No GUI export page is included.
- [x] No Marker integration is included.
- [x] No PDF/Word/HTML export is included.
- [x] No AI, OCR, embedding, vector, or cloud work is included.
- [x] Conversion behavior is unchanged.
- [x] Runner process-control behavior is unchanged.
- [x] Build-library internals are unchanged.
- [x] Search/ranking/aliases/token fallback behavior is unchanged.
- [x] Library-report scoring is unchanged.
- [x] Graph View behavior is unchanged.

Core no-AI path:

- [ ] `office2md --help`
- [ ] `office2md doctor`
- [ ] `office2md doctor-ai` reports AI disabled by default and does not fail if MiniMax/mmx is missing.
- [ ] `office2md convert-file input.pdf output --profile kb`
- [ ] `office2md convert ./input ./output --recursive --profile kb --max-files 5`
- [ ] `office2md convert ./input ./output --recursive --dry-run --include "*.pdf"`

Knowledge Pack files:

- [ ] `document.md`
- [ ] `document.raw.md`
- [ ] `document.json`
- [ ] `manifest.json`
- [ ] `chunks.jsonl`
- [ ] `knowledge.json`
- [ ] `entities.json`
- [ ] `source_map.json`
- [ ] `_index.md`
- [ ] `_index.json`

PDF and drawing support:

- [ ] Docling fallback behavior works when Docling model download fails.
- [ ] MarkItDown fallback writes `fallback_used: true`.
- [ ] `technical_drawing_pdf` classification works.
- [ ] `--render-pdf-pages` writes page images to assets.
- [ ] `document.json.pages` includes page text and image paths.
- [ ] `semantic_title`, `source_page`, and `locator` are separated.
- [ ] `heading_path` does not use `Page N` as the semantic title.

Optional AI behavior:

- [ ] AI is disabled by default.
- [ ] No API key or token is required for no-AI conversion.
- [ ] Missing MiniMax/mmx CLI does not block conversion.
- [ ] `--use-ai --ai-backend cli` can be tested with a mock CLI.
- [ ] AI failure does not block conversion and writes manifest warnings.

rc3 validation evidence:

- [ ] 50-file PDF validation completed with Success 50, Failed 0, Skipped 0.
- [ ] 50-file document kind distribution recorded as `generic_pdf: 45`, `technical_drawing_pdf: 5`.
- [ ] 50-file quality distribution recorded as `low_structure: 42`, `visual_only: 8`.
- [ ] 50-file extraction distribution recorded as `text: 42`, `image_only: 8`.
- [ ] Image-only PDFs are marked with `quality_status: visual_only`.
- [ ] Image-only PDFs are marked with `extraction_status: image_only`.
- [ ] Image-only PDFs are marked with `requires_ocr_or_vision: true`.
- [ ] Image-only source maps retain page image provenance.
- [ ] Optional AI remains disabled and is not required for rc3 validation.

rc4 golden sample validation:

- [ ] Functional Description full-text golden sample records `pages_count: 61`.
- [ ] Functional Description full-text golden sample records `text_pages_count: 61`.
- [ ] Functional Description full-text golden sample records `rendered_pages_count: 10`.
- [ ] Functional Description full-text golden sample records `chunks_count: 167`.
- [ ] Functional Description full-text golden sample records `page_chunks_count: 61`.
- [ ] Functional Description full-text golden sample records `searchable_page_chunks_count: 61`.
- [ ] Functional Description full-text golden sample records `section_chunks_count: 106`.
- [ ] Functional Description full-text golden sample records `section_chunks_with_body_count: 106`.
- [ ] Functional Description evidence distribution is `page: 10`, `text_page: 51`, `section: 106`.
- [ ] Wiring Diagram regression check records `pages_count: 5`, `text_pages_count: 5`, `rendered_pages_count: 5`.
- [ ] Wiring Diagram evidence distribution is `page: 5`.
- [ ] `--max-render-pages` controls image assets only.
- [ ] `--max-text-pages` controls PDF text page extraction.
- [ ] `--extract-all-page-text` extracts text from all PDF pages without rendering all page images.
- [ ] Section-aware reconstruction works for `manual_pdf`, `functional_description_pdf`, and `fault_catalog_pdf`.
- [ ] `source_map.json` supports section provenance through `section_number`, `section_title`, `source_page_start`, and `locator`.
- [ ] Chunk `evidence_type` values are documented as `page`, `text_page`, `section`, and `image`.

rc5 Office validation evidence:

- [ ] `python -m pytest -q` reports 54 passed.
- [ ] `python -m ruff check office2md tests` reports all checks passed.
- [ ] 5-file validation includes `technical_drawing_pdf: 1`.
- [ ] 5-file validation includes `manual_pdf: 1`.
- [ ] 5-file validation includes `process_development_presentation: 1`.
- [ ] 5-file validation includes `mpdp_table_xlsx: 1`.
- [ ] 5-file validation includes `release_rationale_docx: 1`.
- [ ] Wiring Diagram preserves `drawing_number=ENG-186350`.
- [ ] Wiring Diagram preserves `project_number/order_number=SY909735`.
- [ ] Wiring Diagram includes parsed `drawing_index`.
- [ ] Operation Manual Page 1 is `Title Page`.
- [ ] Operation Manual `document_type` is `operating manual`.
- [ ] PPTX chunks use `evidence_type: slide`.
- [ ] PPTX source maps include `slide_number`, `locator`, and `slide_title`.
- [ ] PPTX `document.md` includes `Presentation Summary`, `Key Project Metadata`, `Slide Index`, `Topic Outline`, `Process Development Narrative`, and `Batch Study Summary`.
- [ ] PPTX `batch_study_summary` includes `confidence`, `evidence_slides`, `evidence_snippet`, and `locators`.
- [ ] PPTX batch accuracy check records `VL322673` as `Shake stability fail`, not `pass`.
- [ ] PPTX batch accuracy check records `VL324017` as `Success` with Slide 20 evidence retained.
- [ ] PPTX batch accuracy check does not infer a result status for `VL326528` without direct evidence.
- [ ] PPTX Slide 14 `Feasibility study for Pilot Scale-up` is not classified as `Micro / Risk Assessment`.
- [ ] XLSX chunks use `evidence_type: table`.
- [ ] XLSX MPDP outputs include phase-level `table_section` chunks for PFA / Pilot / Practice / Pre-Production / Production.
- [ ] XLSX source maps include `sheet_name`, `table_name`, `row_start`, and `row_end`.
- [ ] DOCX release rationale metadata is extracted into `knowledge.json`.
- [ ] DOCX release rationale `document.md` includes `Release Summary`, `Key Release Metadata`, `Key Process Parameters`, and `Recommendation`.
- [ ] Office embedded image counts are recorded without exporting Office images.
- [ ] Office missing asset counts and warnings are recorded without blocking conversion.
- [ ] Office image references are counted and warned only; no Office embedded images are extracted in rc5.
- [ ] Real Office image extraction is deferred to Phase 2.9B.

v0.2.0-rc1 Knowledge Library validation evidence:

- [ ] `python -m pytest -q` reports 55 passed.
- [ ] `python -m ruff check office2md tests` reports all checks passed.
- [ ] `office2md build-library` succeeds on the 5-file output root.
- [ ] `library.db` is created with documents, chunks, entities, entity_mentions, assets, relations, documents_fts, and chunks_fts.
- [ ] `library_manifest.json` is created with schema version, input root, counts, warnings count, exports count, and release label.
- [ ] `library_index.json` is created with document/evidence distributions and top entities.
- [ ] `library_graph.json` is created with document/entity/chunk/topic/batch/asset nodes.
- [ ] Markdown portal files are created: `_library.md`, `_documents.md`, `_entities.md`, `_topics.md`, `_batches.md`, `_quality_report.md`.
- [ ] `library-report` prints document kind distribution, evidence type distribution, top entities, top batches, missing assets, low quality documents, and export files.
- [ ] `search-library` returns relevant results for `M4E viscosity`.
- [ ] `search-library` returns relevant results for `VL324017`.
- [ ] `search-library` returns relevant results for `SY909735`.
- [ ] `exports/llamaindex_documents.jsonl` is generated.
- [ ] `exports/haystack_documents.jsonl` is generated.
- [ ] `exports/txtai_rows.jsonl` is generated.
- [ ] `exports/graphrag_input.jsonl` is generated.
- [ ] Each interop export has one row per chunk on the 5-file validation set.
- [ ] Original office2md output root is not modified by `build-library`.
- [ ] LlamaIndex, Haystack, txtai, and GraphRAG are not required dependencies.
- [ ] No AI, OCR, Marker, API, embedding/vector database, or Office image export is used in Phase 3.0.

v0.2.0-rc2 HMI translation and search usability validation evidence:

- [ ] `python -m pytest -q` reports 56 passed.
- [ ] `python -m ruff check office2md tests` reports all checks passed.
- [ ] HMI translation XLSX is detected as `document_kind: hmi_translation_xlsx`.
- [ ] HMI translation XLSX records `quality_status: structured_with_noise`.
- [ ] HMI single-file v2 output includes `hmi_translation_table`, `hmi_translation_group`, and `hmi_translation_row` chunks.
- [ ] HMI group chunks are reduced from 594 to 138 on the CML125 validation sample.
- [ ] HMI row chunks remain available with 250 row chunks.
- [ ] HMI chunks without locator are 0.
- [ ] HMI `document.md` does not include searchable base64-like Internal ID strings.
- [ ] HMI `document.md` does not include repeated `NaN` or all-empty `ref` columns.
- [ ] HMI group headings do not use field/control-level path tokens such as `Textfeld`, `TextField`, `Bildbaustein`, or `Symbolisches EA-Feld`.
- [ ] Library-level chunks are reduced from 1327 to 871 on the CML125 20-file validation library.
- [ ] Library-level `top_entities` aggregates `SY909735` by `normalized_text` and merges `project_number` plus `order_number`.
- [ ] `_library.md` Key Entities lists `SY909735` only once.
- [ ] `_quality_report.md` reports noisy chunks, HMI translation documents, raw text chunks, and chunks without locator.
- [ ] `_quality_report.md` includes search recommendations for HMI translation, drawing index evidence, and excluding translation documents.
- [ ] `locate-document` works with a library output directory.
- [ ] `locate-document` works with `library.db`.
- [ ] `locate-document "Translation"` returns `hmi_translation_xlsx`, 389 chunks, and output directory `copy-of-sy909735-translation-chinese-ver-1`.
- [ ] `search-library` supports `--limit` and `--offset`.
- [ ] `search-library` supports `--kind hmi_translation_xlsx`.
- [ ] `search-library` supports `--evidence drawing_index`.
- [ ] `search-library` supports `--exclude-doc Translation`.
- [ ] `search-library` supports `--has-locator`.
- [ ] `search-library "PLC" --kind hmi_translation_xlsx --limit 20` returns HMI translation results with locators.
- [ ] `search-library "PLC" --evidence drawing_index --kind technical_drawing_pdf --limit 20` returns drawing index results.
- [ ] `search-library "CIP" --exclude-doc Translation --has-locator --limit 20` excludes HMI translation results.
- [ ] `search-library "SY909735" --limit 20` returns relevant CML125/SY909735 results.
- [ ] Windows PowerShell note documents that Office temporary files `~$*` are skipped automatically and that `--exclude "~$*"` should be avoided for now.
- [ ] No AI, OCR, Marker, API, embedding/vector database, or Office image export is used in Phase 3.0.1.

v0.2.0-rc3 100-file validation and duplicate-ID checkpoint evidence:

- [ ] `python -m pytest` reports 57 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] CML125 100-file conversion completes with Success 100, Failed 0, Skipped 0.
- [ ] 100-file manifests record `ocr_used: false` and `ai_used: false`.
- [ ] `office2md build-library` succeeds on the CML125 100-file output root with duplicate checksum files present.
- [ ] 100-file library reports documents 100, chunks 1205, entities 261, warnings 0.
- [ ] 100-file evidence distribution is `drawing_index: 400`, `hmi_translation_group: 138`, `hmi_translation_row: 250`, `hmi_translation_table: 1`, `image: 27`, `page: 248`, `text: 4`, `text_page: 137`.
- [ ] 100-file quality report records noisy chunks 0 and chunks without locator 4.
- [ ] Duplicate checksum outputs receive unique library document IDs without changing non-duplicate document IDs.
- [ ] Duplicate chunk IDs receive unique library chunk IDs while preserving source-map evidence and locators.
- [ ] 100-file review library records 100 distinct document IDs and 1205 distinct chunk IDs.
- [ ] `search-library` smoke tests pass for Translation, SY909735, homogenizer, and alarm.
- [ ] No AI, OCR, Marker, API, embedding/vector database, or Office image export is used in Phase 3.0.2.

v0.2.0-rc4 Phase 3.0.3a quality/search checkpoint evidence:

- [ ] `python -m pytest` reports 60 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] CML125 100-file Phase 3.0.3a library report records `low_quality_documents: 13`.
- [ ] CML125 100-file Phase 3.0.3a library report records `page_level_pdf_documents: 84`.
- [ ] CML125 100-file Phase 3.0.3a library report records `noisy_chunks_count: 0`.
- [ ] Generic PDF subtype refinement classifies obvious datasheet, component, certificate, manual, project book, and report PDFs while leaving uncertain PDFs as `generic_pdf`.
- [ ] Search fallback marks multi-term token fallback in CLI output.
- [ ] `search-library "homogenizer cooling"` returns useful hits with `fallback: token`.
- [ ] `search-library "alarm history"` returns useful hits with `fallback: token`.
- [ ] No AI, OCR, Marker, API, embedding/vector database, or Office image export is used in Phase 3.0.3a.

v0.2.0-rc5 Phase 3.0.4 200-file validation checkpoint evidence:

- [ ] Python version is 3.11.9.
- [ ] `python -m pytest` reports 60 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] CML125 200-file conversion records 200 manifests, 200 success, and 0 failed.
- [ ] CML125 200-file manifests record OCR used 0 and AI used 0.
- [ ] Initial convert hit output-pipe/tool timeout after 103 outputs, then resumed with `--skip-existing` and redirected logs; final output is valid.
- [ ] Manifest warnings are mainly Docling fallback caused by `LocalEntryNotFoundError / WinError 10054`, not OCR or AI usage.
- [ ] `office2md build-library` succeeds with build warnings 0.
- [ ] 200-file library reports documents 200, chunks 1751, entities 267.
- [ ] 200-file document kind distribution is `datasheet_pdf: 112`, `component_document_pdf: 35`, `certificate_pdf: 25`, `manual_pdf: 9`, `generic_pdf: 8`, `technical_drawing_pdf: 4`, `report_pdf: 3`, `document: 2`, `hmi_translation_xlsx: 1`, `project_book_pdf: 1`.
- [ ] 200-file evidence distribution is `drawing_index: 400`, `hmi_translation_group: 138`, `hmi_translation_row: 250`, `hmi_translation_table: 1`, `image: 31`, `page: 508`, `section: 8`, `text: 4`, `text_page: 411`.
- [ ] 200-file quality metrics are `low_quality_documents: 16`, `page_level_pdf_documents: 181`, `noisy_chunks_count: 0`, `noisy_documents: 0`, `chunks_without_locator: 4`, `missing_assets_summary: 0`.
- [ ] Search smoke tests pass for Translation, SY909735, CML125, homogenizer cooling, alarm history, temperature probe, 1V2005, 2M2001, CIP, and seal.
- [ ] Minor `_quality_report.md` extra `_None._` formatting issue is noted as cosmetic follow-up.
- [ ] No AI, OCR, Marker, API, embedding/vector database, Office image export, full-directory validation, or Phase 3.1 work is included.

v0.2.0-rc6 Phase 3.0.5b operational runner checkpoint evidence:

- [ ] `python -m pytest` reports 60 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] `scripts/Invoke-Office2MdChunkedConvert.ps1` supports `-DryRun`.
- [ ] Runner does not delete input files and only creates output/log directories.
- [ ] Runner starts `office2md convert` with `--skip-existing`.
- [ ] Runner redirects stdout and stderr to timestamped logs.
- [ ] Runner checks generated `manifest.json` files against expected output folders and compares against expected unique manifest count.
- [ ] Runner stops only the process tree it launched when an attempt exceeds timeout.
- [ ] Runner supports `-MaxFiles` and `-FullDirectory`.
- [ ] Runner uses `office2md.scanner.scan_input` plus output-directory naming behavior to calculate supported file count and expected unique manifest count.
- [ ] `-MaxFiles 3 -DryRun` reports supported files 598 and expected manifests 3.
- [ ] `-FullDirectory -DryRun` reports supported files 598 and expected unique manifests 588 for the CML125 full source.
- [ ] `docs/ops/cml125_batch_validation.md` documents why the runner exists, when to use it, 300-file and full-directory examples, and OneDrive/on-demand hydration risk.
- [ ] Legacy `.doc` failures remain documented as known unsupported files; no legacy Word conversion dependency is introduced.
- [ ] No AI, OCR, Marker, API, embedding/vector database, Office image export, full-directory validation, or Phase 3.1 work is included.

v0.2.0-rc7 Phase 3.0.6 full-directory validation and runner completion checkpoint evidence:

- [ ] `python -m pytest` reports 61 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] CML125 full-directory validation completes with supported files 598.
- [ ] Runner calculates expected unique manifests 588.
- [ ] Final conversion output contains 589 manifests.
- [ ] Final conversion records 587 success and 2 failed.
- [ ] Failed files are duplicate legacy `Guide to find the devices..doc` inputs.
- [ ] Legacy `.doc` is documented as known unsupported for Phase 3.0.
- [ ] Full-directory manifests record OCR used 0 and AI used 0.
- [ ] `office2md build-library` succeeds.
- [ ] Build warnings are 2, both failed legacy `.doc` manifests.
- [ ] Full-directory library reports documents 587, chunks 4238, entities 365.
- [ ] Full-directory quality metrics include `noisy_chunks_count: 0`.
- [ ] Search smoke and locate-document key checks pass.
- [ ] Runner completion fix requires expected output folders to contain `manifest.json`, not just total manifest count.
- [ ] `-MaxFiles 3 -DryRun` reports supported files 598 and expected unique manifests 3.
- [ ] `-FullDirectory -DryRun` reports supported files 598 and expected unique manifests 588.
- [ ] No AI, OCR, Marker, API, embedding/vector database, Office image export, legacy `.doc` conversion, external conversion dependency, or Phase 3.1 work is included.

v0.2.0-rc8 Phase 3.1a FTS search usability checkpoint evidence:

- [ ] `python -m pytest` reports 62 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] Default `search-library` remains SQLite/FTS based and does not require new flags.
- [ ] Ranking adjustments prefer locator-present chunks and stronger evidence types without removing valid hits.
- [ ] Exact lookups pass for `SY909735`, `1V2005`, and `2M2001`.
- [ ] Token fallback still works for `homogenizer cooling` and `alarm history`.
- [ ] Search output reports mode as `fts` or `token_fallback`.
- [ ] Optional `--facets` works and does not affect default search.
- [ ] Optional `--context` / `--related` works and does not affect default search.
- [ ] Optional `--output-dir` and repeatable `--entity` filters work.
- [ ] Smoke checks pass against the existing CML125 full-directory library for `temperature probe`, `S7-300`, `Operating Manual`, `seal`, and `CIP`.
- [ ] No vector search, embeddings, OCR, AI/MiniMax, cloud/network dependency, Office image export, or SQLite/FTS replacement is included.

v0.2.0-rc10 Phase 3.1c conservative FTS polish checkpoint evidence:

- [ ] `python -m pytest` reports 63 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] Original `search-library` query is tried first.
- [ ] Alias and normalization run only after the original query returns 0 hits.
- [ ] CLI output reports alias or normalized query use.
- [ ] Exact lookups pass without alias/normalization for `SY909735`, `1V2005`, `2M2001`, and `S7-300`.
- [ ] Weak query smoke checks improve for `1THLS200`, `冷却水`, `报警历史`, `密封液`, `操作手册`, `CIP sequence`, `cooling circuit issue`, and `user password`.
- [ ] Existing token fallback still works for `homogenizer cooling` and `alarm history`.
- [ ] Known partial queries remain documented: `vacuum pump fault` and `agitator temperature problem`.
- [ ] No vector search, embeddings, OCR, AI/MiniMax, cloud/network dependency, Office image export, SQLite/FTS replacement, or aggressive synonym expansion is included.

v0.2.0-rc11 Phase 3.1d release-readiness docs checkpoint evidence:

- [ ] `python -m pytest` reports 63 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] README reflects current v0.2.0 capabilities: Knowledge Pack, Library Builder, SQLite/FTS search, token fallback, facets/context/filters, alias/normalization, and chunked/resume runner.
- [ ] README states no OCR, AI/MiniMax, embeddings/vector search, cloud dependency, Office image export, or legacy `.doc` conversion in the validated release path.
- [ ] Known limitations are documented: legacy `.doc` unsupported/fragile, Docling fallback to MarkItDown, Office image export not implemented, and OneDrive full-directory conversion may require the runner.
- [ ] rc10 release notes avoid non-ASCII alias rendering issues in Windows console output.
- [ ] No code changes are included.

v0.2.0 final release evidence:

- [ ] `python -m pytest` reports 63 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] Final validated scope includes Office/PDF/text-like conversion, per-document Knowledge Pack, Knowledge Library Builder, SQLite/FTS `library.db`, `library_index.json`, `library_graph.json`, Markdown portal, interop exports, `library-report`, `search-library`, and `locate-document`.
- [ ] Final search scope includes FTS ranking, token fallback, facets, filters, context/related chunks, and alias/normalization for no-hit queries.
- [ ] Chunked/resume PowerShell runner is included for large OneDrive-backed CML125-style validation.
- [ ] CML125 full-directory validation completed with supported files 598, expected unique manifests 588, final manifests 589, success 587, and failed 2 duplicate legacy `.doc` files.
- [ ] Full-directory validation records OCR used 0 and AI used 0.
- [ ] Full-directory library build succeeds with documents 587, chunks 4238, entities 365, and noisy chunks 0.
- [ ] Known limitations are documented: no OCR, no AI/MiniMax in validated path, no embeddings/vector search, no Office image export, legacy `.doc` unsupported/fragile, Docling fallback to MarkItDown, some Office-derived chunks may lack locators, and OneDrive full-directory conversion may need the runner.
- [ ] Final release notes are written in `RELEASE_NOTES_v0.2.0.md`.

v0.2.1-rc1 optional query diagnostics checkpoint evidence:

- [ ] `python -m pytest` reports 64 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] `search-library --diagnostics` is optional.
- [ ] Default `search-library` output without `--diagnostics` remains unchanged.
- [ ] Diagnostics include original query, effective query, mode, alias/normalization, token fallback status, fallback tokens, filters, result count, top evidence types, top document kinds, locator coverage, and hints.
- [ ] Diagnostics work with aliases, normalized queries, token fallback, `--facets`, `--context`, `--output-dir`, and `--entity`.
- [ ] Smoke diagnostics pass against the existing CML125 full-directory library for `SY909735`, Chinese "cooling water", `1THLS200`, `vacuum pump fault`, `agitator temperature problem`, `homogenizer cooling`, and `alarm history`.
- [ ] No default ranking change, vector search, embeddings, OCR, AI/MiniMax, cloud/network dependency, Office image export, or legacy `.doc` conversion is included.

v0.2.1-rc2 narrow token fallback ranking checkpoint evidence:

- [ ] `python -m pytest` reports 67 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] Token fallback uses a bounded internal candidate pool independent of display `--limit`.
- [ ] Token fallback ranking prefers chunks matching more query tokens.
- [ ] Existing locator, evidence type, and noise ranking preferences are preserved after token coverage.
- [ ] `fault_catalog_pdf` receives a narrow fallback-only boost only for failure-intent tokens such as `fault`, `error`, `alarm`, `problem`, and `trouble`.
- [ ] Normal FTS results are not affected by the fallback-only `fault_catalog_pdf` boost.
- [ ] `vacuum pump fault --limit 10 --diagnostics` returns `Faults and measures catalog_SY909735_AH.pdf`, Page 3 as rank 1.
- [ ] `agitator temperature problem --limit 10 --diagnostics` returns `Faults and measures catalog_SY909735_AH.pdf`, Page 5 and Page 8 as ranks 1 and 2.
- [ ] Exact FTS remains unchanged for `SY909735`, `1V2005`, `2M2001`, and `vacuum pump`.
- [ ] Alias/normalization behavior remains unchanged for Chinese "cooling water" and `1THLS200`.
- [ ] Default CLI output without `--diagnostics` remains the normal search table.
- [ ] No vector search, embeddings, OCR, AI/MiniMax, cloud/network dependency, Office image export, legacy `.doc` conversion, or broadened aliases are included.

v0.2.1-rc3 usability polish checkpoint evidence:

- [ ] `python -m pytest` reports 67 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] `_quality_report.md` no longer prints misleading extra `_None._` after explicit count sections.
- [ ] Quality report cosmetic wording does not change quality metrics or scoring.
- [ ] `docs/usage/common_workflows.md` documents single document conversion, directory conversion, `build-library`, `library-report`, search diagnostics, facets, `--context 2`, `--output-dir`, `--entity`, `locate-document`, and the CML125/OneDrive chunked runner workflow.
- [ ] Common workflow docs note positional `convert INPUT_PATH OUTPUT` and `build-library INPUT_DIR OUTPUT_DIR` syntax.
- [ ] Common workflow docs note PowerShell UTF-8 environment variables and that OCR, AI/MiniMax, embeddings/vector search, cloud services, and Office image export are not used by default.
- [ ] CLI help commands pass for `convert`, `build-library`, `search-library`, `locate-document`, and `library-report`.
- [ ] CLI help wording changes are documentation-only and do not alter CLI behavior.
- [ ] No search ranking, token fallback logic, aliases, vector search, embeddings, OCR, AI/MiniMax, cloud/network dependency, Office image export, or legacy `.doc` conversion changes are included.

v0.2.1 final release evidence:

- [ ] `python -m pytest` reports 67 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] Final scope includes optional `search-library --diagnostics` with default output unchanged.
- [ ] Final scope includes bounded token fallback candidate pool, matched-token coverage ranking, and narrow fallback-only `fault_catalog_pdf` boost for failure-intent tokens.
- [ ] Final scope includes quality report empty-state wording polish, common workflow documentation, and CLI help wording polish.
- [ ] Help commands pass for `convert`, `build-library`, `search-library`, `locate-document`, and `library-report`.
- [ ] CML125 compact smoke checks pass for `SY909735`, Chinese "cooling water", `1THLS200`, `vacuum pump fault`, and `agitator temperature problem` with diagnostics.
- [ ] Exact FTS remains unchanged for known identifier-style queries.
- [ ] No vector search, embeddings, OCR, AI/MiniMax, cloud/network dependency, Office image export, legacy `.doc` conversion, broadened aliases, or exact FTS behavior changes are included.
- [ ] Final release notes are written in `RELEASE_NOTES_v0.2.1.md`.

v0.2.2-rc1 machine-readable search diagnostics checkpoint evidence:

- [ ] `python -m pytest` reports 68 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] `search-library --diagnostics-json` is optional.
- [ ] Default `search-library` output without `--diagnostics-json` remains unchanged.
- [ ] `--diagnostics-json` prints marker line `diagnostics_json:`.
- [ ] `--diagnostics-json` prints stable pretty JSON after normal search tables.
- [ ] Diagnostics JSON includes original query, effective query, mode, alias/normalization fields, token fallback status, fallback tokens, filters, result count, shown count, top evidence types, top document kinds, locator coverage, and hints.
- [ ] Diagnostics JSON includes compact result summaries with rank, chunk ID, document title, source file, document kind, evidence type, locator, and output directory.
- [ ] Diagnostics JSON works with normal output, `--diagnostics`, `--facets`, `--context`, `--output-dir`, and `--entity`.
- [ ] Diagnostics JSON works with alias/normalization and token fallback paths.
- [ ] Smoke JSON checks pass against the existing CML125 full-directory library for `SY909735`, Chinese "cooling water", `1THLS200`, `vacuum pump fault`, and `agitator temperature problem`.
- [ ] Combined smoke JSON checks pass for `SY909735 --diagnostics --diagnostics-json` and `vacuum pump fault --diagnostics --facets --context 2 --diagnostics-json`.
- [ ] No search core, ranking, alias, token fallback logic, vector search, embeddings, OCR, AI/MiniMax, cloud/network dependency, Office image export, or legacy `.doc` conversion changes are included.
- [ ] Release notes are written in `RELEASE_NOTES_v0.2.2-rc1.md`.

v0.2.2-rc2 search result export checkpoint evidence:

- [ ] `python -m pytest` reports 69 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] `search-library --export-json PATH` is optional.
- [ ] Default `search-library` output without `--export-json` remains unchanged.
- [ ] Normal console output still prints when `--export-json` is used.
- [ ] `--export-json` prints an `export_json: <path>` confirmation line when the file is written.
- [ ] Export JSON is UTF-8 pretty JSON.
- [ ] Export JSON parent directories are created automatically.
- [ ] Export JSON includes query metadata, diagnostics summary, result count, shown count, and results.
- [ ] Each exported result includes rank, chunk ID, document title, source file, document kind, evidence type, locator, output directory, and preview.
- [ ] Export works with normal FTS search, token fallback, aliases/normalization, `--diagnostics`, `--diagnostics-json`, `--facets`, `--context`, `--output-dir`, and `--entity`.
- [ ] If `--export-json` is combined with `--diagnostics-json`, diagnostics JSON remains printed last.
- [ ] Smoke export checks pass against the existing CML125 full-directory library for `SY909735`, Chinese "cooling water", and `vacuum pump fault` with diagnostics/context combinations.
- [ ] No search core, ranking, alias, token fallback logic, vector search, embeddings, OCR, AI/MiniMax, cloud/network dependency, Office image export, or legacy `.doc` conversion changes are included.
- [ ] Release notes are written in `RELEASE_NOTES_v0.2.2-rc2.md`.

v0.2.2-rc3 runner final summary checkpoint evidence:

- [ ] `python -m pytest` reports 69 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] Runner final summary is output-only polish.
- [ ] Runner launch command is unchanged.
- [ ] Runner timeout/retry behavior is unchanged.
- [ ] Runner scanner/counting logic is unchanged.
- [ ] Runner conversion behavior is unchanged.
- [ ] Final summary includes input path, output path, log directory, mode, supported file count, expected unique manifest count, final manifest count, completed expected manifest count, failed manifest count, attempts used, timeout/restart count, max attempts, timeout minutes, target reached, final status, log location, and recommended `build-library` command.
- [ ] CML125 `-MaxFiles 3 -DryRun` reports supported files 598, expected unique manifests 3, attempts used 0, and final status `dry-run`.
- [ ] CML125 `-FullDirectory -DryRun` reports supported files 598, expected unique manifests 588, attempts used 0, and final status `dry-run`.
- [ ] Small real `-MaxFiles 1` smoke run prints final summary with completed expected manifests 1/1, failed manifests 0, target reached true, and final status `success`.
- [ ] Existing runner behavior is noted: the timeout branch can print even if a manifest is produced and target is reached; rc3 does not change this because it would alter process-control behavior.
- [ ] No conversion, search core, ranking, alias, token fallback logic, vector search, embeddings, OCR, AI/MiniMax, cloud/network dependency, Office image export, or legacy `.doc` conversion changes are included.
- [ ] Release notes are written in `RELEASE_NOTES_v0.2.2-rc3.md`.

v0.2.2-rc4 CLI help/output consistency checkpoint evidence:

- [ ] `python -m pytest` reports 69 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] CLI changes are help wording only.
- [ ] No runtime behavior changes are included.
- [ ] No search core, ranking, alias, token fallback logic, conversion behavior, runner process-control behavior, output schema, or result ordering changes are included.
- [ ] `build-library` help wording clarifies that it builds from an office2md output root.
- [ ] `search-library --context` / `--related` help explicitly states that the option requires an integer.
- [ ] `search-library --diagnostics-json` help states that JSON is appended after normal output.
- [ ] `search-library --export-json` help states that it writes UTF-8 JSON and creates parent directories.
- [ ] OCR/LLM/AI help wording clarifies that OCR/LLM are not part of the validated path and optional AI is off by default.
- [ ] Representative output audit covers basic search, diagnostics, diagnostics JSON, export JSON, diagnostics/facets/context/export combination, locate-document, library-report, and runner dry-run output.
- [ ] Help commands pass for `convert`, `build-library`, `search-library`, `locate-document`, and `library-report`.
- [ ] No vector search, embeddings, OCR, AI/MiniMax in the validated path, cloud/network dependency, Office image export, or legacy `.doc` conversion changes are included.
- [ ] Release notes are written in `RELEASE_NOTES_v0.2.2-rc4.md`.

v0.2.2 final release evidence:

- [ ] `python -m pytest` reports 69 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] Help commands pass for `convert`, `build-library`, `search-library`, `locate-document`, and `library-report`.
- [ ] Final scope includes optional `search-library --diagnostics-json` with default output unchanged.
- [ ] Final scope includes optional `search-library --export-json PATH` with UTF-8 pretty JSON, automatic parent directory creation, and default output unchanged.
- [ ] Final scope includes output-only runner final summary polish with no launch, timeout/retry, scanner/counting, process-control, resume, or conversion behavior changes.
- [ ] Final scope includes CLI help wording consistency polish only.
- [ ] CML125 compact smoke checks pass for `SY909735`, Chinese "cooling water", `vacuum pump fault`, export JSON, diagnostics/facets/context diagnostics JSON, `locate-document`, and `library-report`.
- [ ] Runner CML125 `-MaxFiles 3 -DryRun` reports supported files 598, expected unique manifests 3, attempts used 0, and final status `dry-run`.
- [ ] No search core, ranking, alias, token fallback logic, conversion behavior, runner process-control behavior, output schema, result ordering, vector search, embeddings, OCR, AI/MiniMax in the validated path, cloud/network dependency, Office image export, or legacy `.doc` conversion changes are included.
- [ ] Final release notes are written in `RELEASE_NOTES_v0.2.2.md`.

v0.2.3-rc1 library-report JSON export checkpoint evidence:

- [ ] `python -m pytest` reports 70 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] `library-report --export-json PATH` is optional.
- [ ] Default `library-report` output without `--export-json` remains unchanged.
- [ ] Normal console output still prints when `--export-json` is used.
- [ ] `--export-json` prints an `export_json: <path>` confirmation line only when the file is written.
- [ ] Export JSON is UTF-8 pretty JSON.
- [ ] Export JSON parent directories are created automatically.
- [ ] Export JSON reuses the existing `library_report()` result dictionary directly.
- [ ] Library-report metrics and scoring are not recalculated differently for JSON.
- [ ] Export JSON includes document/chunk/entity counts, document kind and evidence type distributions, noisy chunk count, chunks without locator, missing assets summary, low quality documents, and page-level PDF documents.
- [ ] README and `docs/usage/common_workflows.md` document `library-report --export-json PATH`.
- [ ] CML125 smoke check confirms default `library-report` has no `export_json:` marker.
- [ ] CML125 smoke export records documents 587, chunks 4238, entities 365, noisy chunks 0, chunks without locator 462, missing assets 0, low quality documents 85, and page-level PDF documents 493.
- [ ] No search core, ranking, alias, token fallback logic, conversion behavior, runner process-control behavior, vector search, embeddings, OCR, AI/MiniMax, cloud/network dependency, Office image export, or legacy `.doc` conversion changes are included.
- [ ] Release notes are written in `RELEASE_NOTES_v0.2.3-rc1.md`.

v0.2.3-rc2 demo/evidence package checkpoint evidence:

- [ ] `python -m pytest` reports 70 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] Changes are docs-only.
- [ ] `docs/usage/demo_evidence_package.md` includes copy-paste PowerShell examples for environment checks, `library-report`, `library-report --export-json`, `search-library --diagnostics-json`, `search-library --export-json`, `locate-document`, and runner `-MaxFiles 3 -DryRun`.
- [ ] `docs/usage/common_workflows.md` links to the demo evidence package.
- [ ] CML125 reference evidence is documented: documents 587, chunks 4238, entities 365, noisy chunks 0, low quality documents 85, page-level PDF documents 493, supported files 598, and expected unique manifests 588.
- [ ] Notes document PowerShell UTF-8 environment variables, quoting paths with spaces, `--context` requiring an integer, no OCR/AI/embedding/vector defaults, and legacy `.doc` unsupported/fragile status.
- [ ] Smoke checks cover `library-report --export-json`, `search-library "vacuum pump fault" --limit 3 --diagnostics-json`, `locate-document "SY909735"`, and runner `-MaxFiles 3 -DryRun`.
- [ ] No code, runtime behavior, search core, ranking, alias, token fallback logic, conversion behavior, runner process-control behavior, library-report metrics/scoring, vector search, embeddings, OCR, AI/MiniMax, cloud/network dependency, Office image export, or legacy `.doc` conversion changes are included.
- [ ] Release notes are written in `RELEASE_NOTES_v0.2.3-rc2.md`.

v0.2.3-rc3 Office-derived locator audit checkpoint evidence:

- [ ] `python -m pytest` reports 70 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] Changes are docs-only audit/report evidence.
- [ ] `docs/design/v023_office_locator_audit.md` records total chunks 4238, chunks with locator 3776, and chunks without locator 462.
- [ ] Missing locators by extension are documented as `.docx: 457`, `.xlsx: 3`, and `.pptx: 2`.
- [ ] Missing locator sources are documented: `Symex CML125 Purchase Agreement_0405.docx` 227, `Symex CML125 Purchase Agreement_to Symex_0404.docx` 227, `CML125 Project.xlsx` 3, `CML125 Area_20171129.pptx` 1, `New Microsoft PowerPoint Presentation.pptx` 1, and three small DOCX files 1 each.
- [ ] Cause analysis records that missing locators are already absent in `chunks.jsonl` and `source_map.json`, `source_map` provenance is `raw_markdown`, generic Office files fall through to `chunk_markdown()`, and the library builder preserves data correctly.
- [ ] Recommendation is E: small report/diagnostic improvement only, with no XLSX/PPTX locator polish yet and no broad Office locator refactor.
- [ ] No code, runtime behavior, conversion logic, Office locator behavior, search core, ranking, alias, token fallback logic, runner process-control behavior, library-report metrics/scoring, vector search, embeddings, OCR, AI/MiniMax, cloud/network dependency, Office image export, legacy `.doc` conversion, or broad Office provenance/locator refactor changes are included.
- [ ] Release notes are written in `RELEASE_NOTES_v0.2.3-rc3.md`.

v0.2.3 final release evidence:

- [ ] `python -m pytest` reports 70 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] Help commands pass for `convert`, `build-library`, `search-library`, `locate-document`, and `library-report`.
- [ ] Final scope includes optional `library-report --export-json PATH` with UTF-8 pretty JSON, automatic parent directory creation, normal console output retained, and default output unchanged.
- [ ] Library-report JSON export reuses the existing `library_report()` result dictionary directly and does not recalculate metrics/scoring differently.
- [ ] Final scope includes docs-only demo/evidence package with copy-paste PowerShell validation examples and CML125 reference evidence.
- [ ] Final scope includes docs-only Office-derived locator audit with recommendation E: small report/diagnostic improvement only, no XLSX/PPTX locator polish yet, and no broad Office locator refactor.
- [ ] CML125 compact smoke checks pass for `library-report`, `library-report --export-json`, `search-library "vacuum pump fault" --limit 3 --diagnostics-json`, `search-library "vacuum pump fault" --limit 3 --export-json`, and `locate-document "SY909735"`.
- [ ] Final library-report JSON smoke records documents 587, chunks 4238, entities 365, noisy chunks 0, chunks without locator 462, low quality documents 85, and page-level PDF documents 493.
- [ ] Runner CML125 `-MaxFiles 3 -DryRun` reports supported files 598, expected unique manifests 3, attempts used 0, and final status `dry-run`.
- [ ] No search core, ranking, alias, token fallback logic, conversion behavior, runner process-control behavior, library-report metrics/scoring, Office locator behavior, vector search, embeddings, OCR, AI/MiniMax, cloud/network dependency, Office image export, legacy `.doc` conversion, or broad Office provenance/locator refactor changes are included.
- [ ] Final release notes are written in `RELEASE_NOTES_v0.2.3.md`.

v0.2.4-rc1 quality / locator report detail polish checkpoint evidence:

- [ ] `python -m pytest` reports 71 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] `library-report` includes chunks without locator total, by document kind, by evidence type, by source extension, and top source files.
- [ ] `library-report --export-json` keeps existing fields and adds only additive missing-locator diagnostic fields.
- [ ] `_quality_report.md` "Chunks Without Locator" section includes the same breakdowns and Office/raw-markdown summary.
- [ ] Report wording states missing locator data is often already absent in `source_map`/chunks and is not a library-builder loss.
- [ ] CML125 smoke records chunks without locator 462, document kind `document: 462`, evidence type `text: 462`, extensions `docx: 457`, `xlsx: 3`, `pptx: 2`, top source `Symex CML125 Purchase Agreement_0405.docx` with 227 chunks, and Office/raw-markdown missing locator total 462.
- [ ] No metric/scoring behavior, conversion behavior, Office locator generation behavior, search core, ranking, alias, token fallback logic, runner process-control behavior, vector search, embeddings, OCR, AI/MiniMax, cloud/network dependency, Office image export, legacy `.doc` conversion, or broad Office provenance/locator refactor changes are included.
- [ ] Release notes are written in `RELEASE_NOTES_v0.2.4-rc1.md`.

v0.2.4 final release evidence:

- [ ] `python -m pytest` reports 71 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] Help commands pass for `convert`, `build-library`, `search-library`, `locate-document`, and `library-report`.
- [ ] Final scope includes reporting/diagnostics polish for chunks without locators in `library-report`, `library-report --export-json`, and `_quality_report.md`.
- [ ] `library-report --export-json` keeps existing fields and adds only additive missing-locator diagnostic fields.
- [ ] Final CML125 smoke records documents 587, chunks 4238, entities 365, chunks without locator 462, document kind `document: 462`, evidence type `text: 462`, extensions `docx: 457`, `xlsx: 3`, `pptx: 2`, top source `Symex CML125 Purchase Agreement_0405.docx` with 227 chunks, noisy chunks 0, and page-level PDF documents 493.
- [ ] Compact smoke checks pass for `library-report`, `library-report --export-json`, `search-library "vacuum pump fault" --limit 3 --diagnostics-json`, `search-library "vacuum pump fault" --limit 3 --export-json`, and `locate-document "SY909735"`.
- [ ] No metric/scoring behavior, conversion behavior, Office locator generation behavior, search core, ranking, alias, token fallback logic, runner process-control behavior, vector search, embeddings, OCR, AI/MiniMax, cloud/network dependency, Office image export, legacy `.doc` conversion, or broad Office provenance/locator refactor changes are included.
- [ ] Final release notes are written in `RELEASE_NOTES_v0.2.4.md`.

v0.3.0-rc1 GUI MVP skeleton checkpoint evidence:

- [ ] `python -m pytest` reports 71 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] `python -m compileall office2md/gui` succeeds.
- [ ] Streamlit is optional only through `[project.optional-dependencies] gui = ["streamlit"]`.
- [ ] Default CLI install and normal CLI use remain unchanged.
- [ ] Optional GUI dependency install with `pip install -e ".[gui]"` succeeds.
- [ ] Streamlit import check reports version 1.57.0.
- [ ] GUI helper import check succeeds for `load_library_report`.
- [ ] GUI app title is `office2md GUI MVP`.
- [ ] Sidebar accepts a Knowledge Library folder or `library.db` path.
- [ ] Library Overview calls the existing `library_report()` functionality.
- [ ] Library Overview displays documents, chunks, entities, noisy chunks, chunks without locator, and page-level PDF document metrics.
- [ ] Missing or invalid library path shows a warning instead of running a workflow.
- [ ] Search, Locate Document, Evidence Package, and Runner Dry-run are placeholders only.
- [ ] `docs/design/v030_gui_mvp_scope.md` defines purpose, scope, phased plan, dependency strategy, validation strategy, and out-of-scope items.
- [ ] `docs/usage/gui_mvp.md` documents optional install, launch command, first screen, current limitations, and no AI/OCR/embedding/vector defaults.
- [ ] No conversion behavior, search core, ranking, alias, token fallback logic, library-report metrics/scoring, runner process-control behavior, vector search, embeddings, OCR, AI/MiniMax, cloud/network dependency, Office image export, or legacy `.doc` conversion changes are included.
- [ ] Release notes are written in `RELEASE_NOTES_v0.3.0-rc1.md`.

v0.3.0-rc2 GUI Search panel checkpoint evidence:

- [ ] `python -m pytest` reports 72 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] `python -m compileall office2md/gui` succeeds.
- [ ] GUI helper import check succeeds for `load_library_report`.
- [ ] Streamlit import check reports version 1.57.0.
- [ ] GUI Search panel is read-only.
- [ ] Search controls include query, limit default 5, diagnostics checkbox, facets checkbox, context integer default 0, optional output directory filter, and optional entity filter.
- [ ] Search panel calls existing `search_library()`, `search_library_diagnostics()`, and `search_library_facets()` functions.
- [ ] Result table includes rank, document title, source file, document kind, evidence type, locator, output directory, and preview.
- [ ] Diagnostics display includes mode, effective query, alias/normalization fields, token fallback status and tokens, result count, shown count, locator coverage, and hints.
- [ ] Facets display includes document kind, evidence type, source file, and output directory facets when available.
- [ ] Related chunks display when context is greater than 0.
- [ ] Error handling covers invalid library path, empty query, no results, and search errors.
- [ ] `Download search JSON` button reuses the existing CLI search export payload shape.
- [ ] CLI `--export-json` schema is unchanged.
- [ ] `docs/usage/gui_mvp.md` and `docs/design/v030_gui_mvp_scope.md` document the Search panel.
- [ ] Helper-level CML125 smoke checks pass for `vacuum pump fault`, Chinese `cooling water`, and `SY909735`.
- [ ] No Locate Document GUI implementation, Evidence Package GUI implementation, Runner Dry-run GUI implementation, search core, ranking, alias, token fallback logic, diagnostics semantics, CLI export schema, conversion behavior, library-report metrics/scoring, runner process-control behavior, vector search, embeddings, OCR, AI/MiniMax, cloud/network dependency, Office image export, or legacy `.doc` conversion changes are included.
- [ ] Release notes are written in `RELEASE_NOTES_v0.3.0-rc2.md`.

v0.3.0-rc3 GUI Graph View MVP checkpoint evidence:

- [ ] `python -m pytest` reports 73 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] `python -m compileall office2md/gui` succeeds.
- [ ] Streamlit import check reports version 1.57.0.
- [ ] Pyvis import check succeeds.
- [ ] GUI helper import check succeeds for `load_library_report`.
- [ ] `pyvis` is optional only through the `gui` extra.
- [ ] Default CLI install and normal CLI use remain unchanged.
- [ ] Default graph mode is Curated Knowledge Graph.
- [ ] Curated Knowledge Graph shows GUI-side curated concepts only.
- [ ] Curated graph filters noisy raw labels such as language codes, standalone units, pure years, `User Texts`, source/page/asset labels, and raw provenance edge types.
- [ ] Useful concepts are present in CML125 smoke where found, including operation manual, maintenance, fault, cooling water, PLC, agitator, cleaning, CIP, sealing liquid, vacuum pump, VFD, alarm, valve, and temperature probe.
- [ ] Keyword filtering searches concept labels, aliases, document titles, and chunk/document context.
- [ ] Keyword smoke works for maintenance, cooling water, vacuum pump, alarm, and operation manual.
- [ ] Edge labels are hidden by default.
- [ ] `Show edge labels` checkbox exists and explicitly enables edge labels.
- [ ] Edge type and weight remain available in hover/title metadata.
- [ ] Graph layout uses randomSeed 42, stabilization, calmer physics, capped node sizing, capped edge width, and no directed arrows.
- [ ] Document-Concept Graph remains available.
- [ ] Raw Provenance Graph remains available as debug/provenance mode.
- [ ] Helper-level CML125 smoke confirms Curated Knowledge Graph 26 nodes and 194 edges, Document-Concept Graph availability, and Raw Provenance Graph bounded rendering.
- [ ] No Build/Update Library workflow, Locate Document panel, Evidence Package panel, Runner Dry-run panel, search core, ranking, alias, token fallback logic, conversion behavior, library-report metrics/scoring, runner process-control behavior, library builder graph generation, vector search, embeddings, OCR, AI/MiniMax, cloud/network dependency, Office image export, or legacy `.doc` conversion changes are included.
- [ ] Release notes are written in `RELEASE_NOTES_v0.3.0-rc3.md`.

v0.3.0-rc4 GUI Build / Update Library Scan / Dry-run checkpoint evidence:

- [ ] `python -m pytest` reports 74 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] `python -m compileall office2md/gui` succeeds.
- [ ] Streamlit import check reports version 1.57.0.
- [ ] Pyvis import check succeeds.
- [ ] GUI helper import check succeeds for `load_library_report`.
- [ ] GUI page `Build / Update Library` exists.
- [ ] Inputs include source folder, conversion output folder, library output folder, log folder, MaxFiles / FullDirectory selection, skip-existing default, render PDF pages default, and no OCR/no AI notes.
- [ ] Scan / Dry-run uses existing `office2md.scanner.scan_input()` scanner logic.
- [ ] Scan / Dry-run does not convert files, build a library, execute the runner, or create/delete output or log folders.
- [ ] Scan / Dry-run counts supported files, applies MaxFiles / FullDirectory selection, calculates expected unique manifests, counts existing manifests, counts completed expected manifests, counts failed manifests, and reports target completion status.
- [ ] Warnings cover OneDrive/Teams offline availability, network path slowness/locks, legacy `.doc` unsupported/fragile status, dry-run-only behavior, and no OCR/no AI defaults.
- [ ] Command previews are generated for the PowerShell chunked runner and `build-library`, using selected paths and options, and are not executed.
- [ ] CML125 helper smoke records supported files 598, MaxFiles 3 selected target 3, MaxFiles 3 expected unique manifests 3, full-directory expected unique manifests 588, existing manifests 589, and full-directory completed expected manifests 588.
- [ ] `docs/usage/gui_mvp.md`, `docs/design/v030_gui_mvp_scope.md`, and `docs/design/v030_build_update_library_workflow.md` document the Scan / Dry-run panel.
- [ ] No Convert / Update execution, Build Library execution, Load Built Library, conversion behavior, runner process-control behavior, scanner behavior, output directory naming behavior, search core, ranking, alias, token fallback logic, library-report metrics/scoring, library builder behavior, vector search, embeddings, OCR, AI/MiniMax, cloud/network dependency, direct Teams/SharePoint API integration, Office image export, or legacy `.doc` conversion changes are included.
- [ ] Release notes are written in `RELEASE_NOTES_v0.3.0-rc4.md`.

v0.3.0-rc5 GUI Convert / Update checkpoint evidence:

- [ ] `python -m pytest` reports 75 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] `python -m compileall office2md/gui` succeeds.
- [ ] Streamlit import check reports version 1.57.0.
- [ ] Pyvis import check succeeds.
- [ ] GUI helper import check succeeds for `load_library_report`.
- [ ] Build / Update Library page includes a Convert / Update section.
- [ ] Convert / Update uses the existing `scripts/Invoke-Office2MdChunkedConvert.ps1` runner.
- [ ] Explicit safety confirmation is required before execution.
- [ ] UI shows exact PowerShell runner command, source folder, conversion output folder, log folder, MaxFiles / FullDirectory mode, timeout minutes, max attempts, skip-existing status, render options, and no OCR/no AI notes.
- [ ] Execution captures and displays stdout, stderr, exit code, log folder, final manifest count, and failed manifest count.
- [ ] `build-library` remains a preview/manual next command only.
- [ ] No automatic `build-library` execution is included.
- [ ] No automatic library loading is included.
- [ ] Runner script is unchanged.
- [ ] Conversion behavior is unchanged.
- [ ] CML125 conversion was not executed.
- [ ] Safe temporary MaxFiles 1 runner smoke exits 0, creates output/log folders through the runner, records final manifest count 1, and failed manifest count 0.
- [ ] CML125 command preview smoke generates a MaxFiles 3 command with selected paths, `-TimeoutMinutes 45`, `-MaxAttempts 20`, and `-MaxFiles 3`.
- [ ] `docs/usage/gui_mvp.md`, `docs/design/v030_gui_mvp_scope.md`, and `docs/design/v030_build_update_library_workflow.md` document the Convert / Update panel.
- [ ] No Build Library execution, Load Built Library, one-click full workflow, runner process-control behavior, conversion behavior, scanner behavior, output directory naming behavior, search core, ranking, alias, token fallback logic, library-report metrics/scoring, library builder behavior, vector search, embeddings, OCR, AI/MiniMax, cloud/network dependency, direct Teams/SharePoint API integration, Office image export, or legacy `.doc` conversion changes are included.
- [ ] Release notes are written in `RELEASE_NOTES_v0.3.0-rc5.md`.

v0.3.0-rc6 GUI Build Library and Load Built Library checkpoint evidence:

- [ ] `python -m pytest` reports 76 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] `python -m compileall office2md/gui` succeeds.
- [ ] Streamlit import check reports version 1.57.0.
- [ ] Pyvis import check succeeds.
- [ ] GUI helper import check succeeds for `load_library_report`.
- [ ] Build / Update Library page includes a Build Library section.
- [ ] UI labels Source Folder as original documents, Conversion Output Folder as per-document Knowledge Pack outputs, and Library Output Folder as final searchable library with `library.db`.
- [ ] UI states that the Conversion Output Folder is not directly readable as a Library and that users should run Build Library first, then load the Library Output Folder.
- [ ] Build Library shows exact `python -m office2md.cli build-library <conversion_output> <library_output>` command preview.
- [ ] Build Library requires safety confirmation before execution.
- [ ] Build Library uses existing CLI via subprocess, captures stdout/stderr and exit code, displays library output summary, and does not hide failures.
- [ ] Successful build summary includes `library.db`, `library_index.json`, `library_graph.json`, `_library.md`, `_quality_report.md`, and report counts when available.
- [ ] Load Built Library validates `library.db`, sets GUI session Library path to the Library Output Folder, and warns clearly when the selected folder does not look like a built library.
- [ ] No one-click full workflow is included.
- [ ] Convert / Update still does not auto-run build-library.
- [ ] Build-library internals are unchanged.
- [ ] Conversion, runner, search, and report behavior are unchanged.
- [ ] Safe temporary smoke converts `tests/fixtures/sample.txt` through the existing runner, then runs Build Library explicitly.
- [ ] Safe smoke records conversion exit code 0, final manifests 1, failed manifests 0, build-library exit code 0, `library.db`, `library_index.json`, `library_graph.json`, `_library.md`, `_quality_report.md`, and `library_report()` counts documents 1, chunks 2, entities 0.
- [ ] CML125 preview confirms build-library command for `Symex_CML125_validation_full` to `Symex_CML125_library_full`; full CML125 was not rebuilt.
- [ ] `docs/usage/gui_mvp.md`, `docs/design/v030_gui_mvp_scope.md`, and `docs/design/v030_build_update_library_workflow.md` document Build Library and Load Built Library.
- [ ] No automatic conversion before build-library, automatic deletion/overwrite behavior, conversion behavior, runner process-control behavior, build-library internals, search core, ranking, alias, token fallback logic, library-report metrics/scoring, vector search, embeddings, OCR, AI/MiniMax, cloud/network dependency, direct Teams/SharePoint API integration, Office image export, or legacy `.doc` conversion changes are included.
- [ ] Release notes are written in `RELEASE_NOTES_v0.3.0-rc6.md`.

v0.3.0-rc7 Output Workspace and Library-Native Knowledge Graph quality checkpoint evidence:

- [ ] `python -m pytest` reports 77 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] `python -m compileall office2md/gui` succeeds.
- [ ] Streamlit import check reports version 1.57.0.
- [ ] Pyvis import check succeeds.
- [ ] GUI helper import check succeeds for `load_library_report`.
- [ ] Build / Update Library uses one user-facing Output Workspace Folder.
- [ ] GUI derives `<workspace>\conversion`, `<workspace>\library`, and `<workspace>\logs`.
- [ ] Convert / Update uses `<workspace>\conversion` and `<workspace>\logs`.
- [ ] Build Library uses `<workspace>\conversion` to `<workspace>\library`.
- [ ] Load Built Library loads `<workspace>\library`.
- [ ] Load Built Library uses a pending session value and rerun flow instead of directly mutating the Library path widget key after instantiation.
- [ ] The GUI warns when a selected Library path looks like a conversion output folder instead of a built library.
- [ ] Default Graph View is `Knowledge Graph`.
- [ ] Knowledge Graph extracts library-native concepts from current library data instead of a fixed equipment vocabulary.
- [ ] Concept quality filtering removes low-value fragments such as `Cover`, `Sheet`, `Cover Sheet`, `Private confidential`, `Liang private`, `Selection new`, and `Caner sheet`.
- [ ] Concept quality filtering avoids false splits such as `HPLC` to `PLC` and `Participated` to `CIP`.
- [ ] Interview/resume library smoke confirms useful library-native concepts can appear when supported by the library, including Food science, Drug discovery, Quality risk, Packaging Selection, and Risk Level.
- [ ] CML125 library smoke confirms Knowledge Graph still renders and does not show raw provenance noise in the default graph.
- [ ] Document-Concept Graph remains available.
- [ ] Raw Provenance Graph remains available as debug/provenance mode.
- [ ] Safe temporary workspace smoke confirms conversion exit code 0, final manifests 1, failed manifests 0, build-library exit code 0, and a valid `<workspace>\library` with documents 1, chunks 2, entities 0.
- [ ] No one-click full workflow, automatic deletion/cleanup, conversion behavior, runner process-control behavior, build-library internals, search core, ranking, alias, token fallback logic, library-report metrics/scoring, vector search, embeddings, OCR, AI/MiniMax, cloud/network dependency, direct Teams/SharePoint API integration, Office image export, or legacy `.doc` conversion changes are included.
- [ ] Release notes are written in `RELEASE_NOTES_v0.3.0-rc7.md`.

v0.3.1 release documentation patch evidence:

- [ ] `v0.3.0` exists locally.
- [ ] `v0.3.0` exists on remote `origin`.
- [ ] `v0.3.0` tag was not moved or recreated.
- [ ] `README.md` contains the exact phrase `AI enrichment is opt-in`.
- [ ] `README.md` contains the exact phrase `MiniMax CLI is not required`.
- [ ] `RELEASE_NOTES_v0.3.0.md` exists and matches the README release notes link.
- [ ] `RELEASE_NOTES_v0.3.1.md` records the documentation-only patch release.
- [ ] `pyproject.toml` version is updated to `0.3.1`.
- [ ] `python -m pytest` reports all tests passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] `python -m compileall office2md/gui` succeeds.
- [ ] CLI help checks pass for convert, build-library, search-library, locate-document, and library-report.
- [ ] No conversion behavior, runner process-control behavior, build-library internals, search core/ranking/aliases/token fallback, Graph View behavior, library-report scoring, Marker integration, Obsidian export, AI/OCR/embedding/vector/cloud behavior changes are included.
- [ ] Release notes are written in `RELEASE_NOTES_v0.3.1.md`.

v0.4.1-rc3 GUI product presentation polish checkpoint evidence:

- [ ] `python -m pytest` reports 141 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] `python -m compileall office2md/gui` succeeds.
- [ ] CLI help checks pass for workspace-status, workspace-init, workspace-scan, workspace-register-library, workspace-register-output, export-obsidian, convert, build-library, search-library, locate-document, and library-report.
- [ ] Main GUI title is `office2md Local Knowledge Workspace`.
- [ ] Sidebar labels include `Library`, `Knowledge Graph`, `Build / Update`, `Workspace Status`, and `Find Document`.
- [ ] Internal GUI routing remains stable through product labels mapped to existing route identifiers.
- [ ] Workspace Status uses friendlier summary metrics and table rows instead of raw top-level debug JSON blocks.
- [ ] Detailed workspace data remains available through `Workspace details` and `Download workspace status JSON`.
- [ ] Init-only workspaces no longer show empty trace arrows such as `sha256:... -> ->`.
- [ ] Empty source/library/output states use clear product wording.
- [ ] Next-step commands are shown as a guided workflow: scan sources, register library, register output.
- [ ] Non-workspace path hints remain unchanged.
- [ ] Workspace Status remains read-only with no subprocess, automatic workspace-init, automatic workspace-scan, conversion, build-library, export, manifest writes, or source/output file modifications.
- [ ] No OfficeCLI integration, new conversion engines, conversion behavior changes, runner behavior changes, build-library internals changes, search/ranking changes, Graph View behavior changes, Obsidian export behavior changes, Wiki editing workflow, AI/OCR/Marker/vector/cloud work, or workspace CLI behavior changes are included.
- [ ] Release notes are written in `RELEASE_NOTES_v0.4.1-rc3.md`.

v0.4.1 final release readiness evidence:

- [ ] `pyproject.toml` version is updated to `0.4.1`.
- [ ] `office2md.__version__` is updated to `0.4.1`.
- [ ] `python -m pytest` reports 141 passed.
- [ ] `python -m ruff check .` reports all checks passed.
- [ ] `python -m compileall office2md/gui` succeeds.
- [ ] CLI help checks pass for workspace-init, workspace-scan, workspace-register-library, workspace-register-output, workspace-status, export-obsidian, convert, build-library, search-library, locate-document, and library-report.
- [ ] GUI title is `office2md Local Knowledge Workspace`.
- [ ] Sidebar labels are product-facing.
- [ ] Workspace Status page exists and remains read-only.
- [ ] Workspace Root Path guidance is clear.
- [ ] Library Path versus Workspace Root Path distinction is clear.
- [ ] Init-only workspace status is valid and readable.
- [ ] Empty source/library/output states use friendly wording.
- [ ] Incomplete traceability state does not show empty arrows.
- [ ] Next-step commands are shown as a guided workflow.
- [ ] Download workspace status JSON remains available.
- [ ] Non-workspace paths show expected workspace markers and workspace-init command hints.
- [ ] Built library, Obsidian export, conversion / Knowledge Pack-like, and `*-office2md-output` path hints work.
- [ ] Existing workspace CLI commands remain unchanged.
- [ ] Existing non-workspace commands and GUI pages remain unaffected.
- [ ] OfficeCLI benchmark plan is documentation only.
- [ ] No OfficeCLI integration or dependency is included.
- [ ] No Wiki editing workflow, AI suggestions, Marker integration, AI/OCR/embedding/vector/cloud work, conversion behavior changes, runner behavior changes, build-library internals changes, search/ranking changes, Graph View behavior changes, Obsidian export behavior changes, or GUI workspace file modifications are included.
- [ ] Release notes are written in `RELEASE_NOTES_v0.4.1.md`.
