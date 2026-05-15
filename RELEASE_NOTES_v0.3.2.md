# office2md v0.3.2 Release Notes

Status: final v0.3.2 release.

## Scope

v0.3.2 adds local Obsidian export support across both CLI and GUI workflows.

This release does not add asset copying, Marker integration, PDF/Word/HTML export, AI, OCR, embeddings, vector search, cloud features, v0.4 workspace layers, conversion changes, runner process-control changes, build-library changes, search/ranking changes, Graph View changes, or library-report scoring changes.

## CLI Obsidian Export

```powershell
python -m office2md.cli export-obsidian LIBRARY_PATH VAULT_OUTPUT
```

Options:

- `--overwrite`
- `--dry-run`
- `--max-concepts`
- `--max-evidence-per-concept`

`LIBRARY_PATH` accepts either a built library folder or a direct `library.db` path.

The CLI export creates:

```text
VAULT_OUTPUT/
  00_Index.md
  00_Library_Report.md
  Documents/
  Concepts/
  _office2md/
    export_manifest.json
```

Document notes include YAML frontmatter, Related Concepts, and Obsidian `[[wikilinks]]`.

Concept notes include YAML frontmatter, Related Documents, and Obsidian `[[wikilinks]]`.

`export_manifest.json` records export type, office2md version, paths, counts, warnings, and options.

Safety behavior:

- non-empty output folders fail unless `--overwrite` is provided;
- `--dry-run` reports planned export counts without writing files.

## GUI Export Page

The Streamlit GUI now includes:

- `Export`
- `Export to Obsidian Vault`

The page exposes:

- Current Library Path;
- Obsidian Vault Output Folder;
- Max Concepts;
- Max Evidence Per Concept;
- Overwrite existing output;
- Dry-run;
- Preview Export;
- Export to Obsidian.

Preview Export uses dry-run behavior. Export to Obsidian reuses the existing exporter implementation directly and shows the equivalent CLI command, output path, counts, warnings, generated structure, and parsed manifest summary after a real export.

## Product Behavior

- Obsidian does not need to be installed to generate the vault folder.
- The exported folder can later be opened as an Obsidian vault.
- Assets are intentionally not copied in this MVP; manifests record a warning when source-library assets exist.
- Concept extraction is heuristic and library-native. It uses current-library content rather than a fixed equipment vocabulary and may need tuning after real-use review.

## Validation

- `python -m pytest`
- `python -m ruff check .`
- `python -m compileall office2md/gui`
- CLI help checks:
  - `export-obsidian`
  - `convert`
  - `build-library`
  - `search-library`
  - `locate-document`
  - `library-report`
- Tiny fixture export smoke
- Tiny fixture GUI/helper export smoke
- CML125 dry-run Obsidian export smoke
- CML125 search smoke for `vacuum pump fault`
