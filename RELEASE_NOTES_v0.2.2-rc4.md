# office2md v0.2.2-rc4 Release Notes

v0.2.2-rc4 is a CLI help and output consistency checkpoint after the v0.2.2-rc1 through v0.2.2-rc3 search and runner output additions.

This checkpoint changes help wording only. It does not change runtime behavior, search behavior, result ordering, output schemas, conversion behavior, runner process-control behavior, ranking, aliases, or token fallback logic.

It does not add vector search, embeddings, OCR, AI/MiniMax, cloud/network dependencies, Office image export, or legacy `.doc` conversion.

## CLI Help Polish

Help wording was clarified for:

- `build-library`: description now refers to building from an office2md output root.
- `search-library --context` / `--related`: help now explicitly says the option requires an integer.
- `search-library --diagnostics-json`: help now says the JSON is appended after normal output.
- `search-library --export-json`: help now says it writes UTF-8 JSON and creates parent directories.
- conversion AI/OCR/LLM flags: help now clarifies that optional AI is off by default and that OCR/LLM reserved flags are not part of the validated path.

No option names, defaults, schemas, or command behavior changed.

## Output Audit

Representative CLI output was reviewed for:

- `search-library` basic output
- `search-library --diagnostics`
- `search-library --diagnostics-json`
- `search-library --export-json`
- `search-library --diagnostics --facets --context 2 --export-json`
- `locate-document`
- `library-report`
- runner `-MaxFiles 3 -DryRun`

No output schema or result ordering changes were made.

## Validation

```bash
python -m pytest
69 passed

python -m ruff check .
All checks passed!
```

Help commands passed for:

- `python -m office2md.cli convert --help`
- `python -m office2md.cli build-library --help`
- `python -m office2md.cli search-library --help`
- `python -m office2md.cli locate-document --help`
- `python -m office2md.cli library-report --help`

## Explicit Non-Goals

v0.2.2-rc4 does not include:

- runtime behavior changes
- output schema changes
- result ordering changes
- search core changes
- ranking changes
- alias changes
- token fallback logic changes
- conversion behavior changes
- runner process-control changes
- vector search
- embeddings
- OCR
- AI/MiniMax
- cloud/network dependency
- Office image export
- legacy `.doc` conversion
