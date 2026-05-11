# Obsidian Export

Export an existing built office2md Knowledge Library to a local Obsidian-friendly vault folder:

```powershell
python -m office2md.cli export-obsidian "C:\path\to\library" "C:\path\to\obsidian-vault"
```

You can pass either a built library folder or a direct `library.db` path:

```powershell
python -m office2md.cli export-obsidian "C:\path\to\library\library.db" "C:\path\to\obsidian-vault"
```

The command creates:

```text
obsidian-vault/
  00_Index.md
  00_Library_Report.md
  Documents/
  Concepts/
  _office2md/
    export_manifest.json
```

## Options

```powershell
python -m office2md.cli export-obsidian "C:\path\to\library" "C:\path\to\vault" --dry-run
python -m office2md.cli export-obsidian "C:\path\to\library" "C:\path\to\vault" --overwrite
python -m office2md.cli export-obsidian "C:\path\to\library" "C:\path\to\vault" --max-concepts 50 --max-evidence-per-concept 3
```

- `--dry-run` reports planned document and concept counts without writing files.
- `--overwrite` allows replacing a non-empty output folder.
- `--max-concepts` limits concept notes, default `100`.
- `--max-evidence-per-concept` limits snippets in each concept note, default `5`.

## Behavior

Document notes include YAML frontmatter and a Related Concepts section using `[[wikilinks]]`.

Concept notes include YAML frontmatter and a Related Documents section using `[[wikilinks]]`.

Concepts are extracted from the built library content itself, using entities, document titles, headings, and chunk text. The export does not use a fixed equipment vocabulary.

Assets are not copied in this MVP. If the library has assets, `_office2md/export_manifest.json` records a warning.

Obsidian does not need to be installed to run the export.
