# office2md v0.3.2-rc2 Release Notes

Status: release candidate for v0.3.2 P2.

## Scope

v0.3.2-rc2 adds the optional GUI Export to Obsidian page on top of the existing v0.3.2-rc1 local exporter.

This checkpoint does not add asset copying, Marker integration, PDF/Word/HTML export, AI, OCR, embeddings, vector search, cloud features, v0.4 workspace layers, conversion changes, runner process-control changes, build-library changes, search/ranking changes, Graph View changes, or library-report scoring changes.

## GUI Export Page

The Streamlit sidebar now includes:

- `Export`

The page includes:

- `Export to Obsidian Vault`
- Current Library Path, defaulted from the loaded GUI library path
- Obsidian Vault Output Folder
- Max Concepts
- Max Evidence Per Concept
- Overwrite existing output
- Dry-run
- `Preview Export`
- `Export to Obsidian`

## Behavior

- Preview Export always uses dry-run behavior and does not write files.
- Export to Obsidian calls the existing `office2md.exports.obsidian.export_obsidian()` implementation directly.
- The GUI does not duplicate the exporter.
- Obsidian does not need to be installed to generate the vault folder.
- The exported folder can be opened in Obsidian later.
- The page shows the equivalent CLI command, output path, document/concept counts, warnings, expected vault structure, and parsed export manifest after a real export.

User-facing text also states:

- assets are not copied in this MVP;
- concept extraction remains heuristic/library-native and may need real-use tuning.

## CLI Compatibility

The CLI contract is unchanged:

```powershell
python -m office2md.cli export-obsidian LIBRARY_PATH VAULT_OUTPUT
```

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
- Tiny fixture GUI/helper smoke:
  - convert `tests/fixtures/sample.txt`
  - build library
  - export through `run_obsidian_export_for_gui()`
  - confirm expected vault files and parsed manifest with `export_type: obsidian`
- CML125 helper dry-run:
  - planned documents `587`
  - planned concepts bounded to `20`
  - uncopied asset warning recorded
  - no full vault created
