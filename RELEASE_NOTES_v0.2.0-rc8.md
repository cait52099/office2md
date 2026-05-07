# office2md v0.2.0-rc8 Release Notes

Release candidate focused on Phase 3.1a: FTS search usability improvements on top of the validated Phase 3.0 full-directory library.

v0.2.0-rc8 keeps SQLite/FTS as the search engine. It does not add vector search, embeddings, OCR, AI/MiniMax, cloud/network dependencies, Office image export, legacy `.doc` conversion, or Phase 3.1 embedding work.

## Search Usability

Improved `search-library` without changing the validated library build pipeline:

- ranking adjustments prefer locator-present chunks
- ranking adjustments prefer stronger evidence types such as `page`, `text_page`, `hmi_translation_*`, and `drawing_index`
- exact lookup behavior remains reliable for `SY909735`, `1V2005`, and `2M2001`
- token fallback remains active for zero-hit multi-term queries such as `homogenizer cooling` and `alarm history`
- search output now shows mode explicitly: `fts` or `token_fallback`
- previews focus on any matching query token, not only the first token

## Optional Search Controls

Added optional CLI controls:

- `--facets` to print document kind, evidence type, source file, output dir, has-locator, and entity counts
- `--output-dir` to filter by output directory name
- repeatable `--entity` to filter by entity text
- `--context` / `--related` to show nearby chunks from the same document

These controls are optional and do not affect default search behavior.

## Validation

```bash
python -m pytest
62 passed

python -m ruff check .
All checks passed!
```

Smoke checks against the existing CML125 full-directory library passed for:

- `SY909735`
- `1V2005`
- `2M2001`
- `homogenizer cooling`
- `alarm history`
- `temperature probe`
- `S7-300`
- `Operating Manual`
- `seal`
- `CIP`

`--facets`, `--context`, `--entity`, and `--output-dir` were also smoke-tested against the existing full-directory library.

## Explicit Non-Goals

v0.2.0-rc8 does not add:

- vector search
- embeddings
- OCR
- AI/MiniMax
- cloud or network dependency
- Office image export
- SQLite/FTS replacement
