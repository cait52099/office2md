# v0.2.1 Backlog

Baseline: `v0.2.0`

v0.2.0 is complete and validated on the full CML125 directory. The v0.2.1 backlog should stay conservative: no OCR, AI/MiniMax, embeddings/vector search, cloud/network dependency, Office image export, or legacy `.doc` conversion.

## Baseline Validation

- pytest: 63 passed
- ruff: all checks passed
- CML125 full-directory validation completed
- supported files: 598
- success: 587
- failed: 2 duplicate legacy `.doc` files
- OCR used: 0
- AI used: 0
- library documents: 587
- chunks: 4238
- entities: 365
- noisy_chunks_count: 0

## P0 Release Blockers

No P0 release blockers are currently identified for v0.2.1.

The v0.2.0 release is clean, tagged, and validated. v0.2.1 should be a polish release unless a new validation dataset reveals a regression.

## P1 Small High-Value Polish

### 1. Query Diagnostics

- Problem: Weak or partial searches do not explain which tokens matched, which aliases were used, or which tokens were missing.
- Proposed solution: Add optional `search-library --diagnostics` output showing original query, query used, alias/normalization, token list, matched tokens per top result, and missing tokens.
- Expected files touched: `office2md/library.py`, `office2md/cli.py`, `tests/test_library_builder.py`, README examples.
- Risk level: Low. Optional flag only; default search remains unchanged.
- Validation method: Unit tests for diagnostics fields; smoke tests for `vacuum pump fault`, `agitator temperature problem`, `homogenizer cooling`, and exact part numbers.
- v0.2.1 decision: Include.

### 2. Alias and Ranking Polish for Remaining Weak Queries

- Problem: `vacuum pump fault` and `agitator temperature problem` still return partial results because current token fallback finds related terms but does not strongly bind them into the same context.
- Proposed solution: Add narrow, deterministic query expansion and ranking boosts only when the original query has 0 hits or token fallback is used. Prefer chunks where key terms occur in the same chunk, same HMI group, same page, or same document section.
- Expected files touched: `office2md/library.py`, `tests/test_library_builder.py`, possibly README search examples.
- Risk level: Medium. Ranking changes can reorder useful exact or HMI results if too broad.
- Validation method: Before/after smoke set for exact queries (`SY909735`, `1V2005`, `2M2001`, `S7-300`), weak queries, and bilingual aliases.
- v0.2.1 decision: Include, but keep aliases conservative.

### 3. Quality Report Formatting Polish

- Problem: Earlier reviews noted minor cosmetic formatting such as `_None._` presentation and dense quality sections.
- Proposed solution: Clean up `_quality_report.md` formatting without changing quality metrics or scoring logic.
- Expected files touched: `office2md/library.py`, tests covering quality report text.
- Risk level: Low.
- Validation method: Unit tests for report sections; rebuild or inspect existing library report if needed.
- v0.2.1 decision: Include.

### 4. Documentation Examples for Common Workflows

- Problem: README is accurate but dense. Common workflows such as "convert CML125 subset", "build library", "search with facets/context", and "resume large OneDrive run" could be easier to follow.
- Proposed solution: Add a concise workflow document with copy-paste PowerShell commands and expected outputs.
- Expected files touched: `docs/ops/` or `docs/design/`, README cross-link.
- Risk level: Low.
- Validation method: Docs review plus command syntax check against CLI help.
- v0.2.1 decision: Include.

## P2 Useful But Non-Urgent Improvements

### 5. Office-Derived Chunk Locator Polish

- Problem: Some Office-derived chunks can lack precise locators. This is known and not blocking, but locator quality affects search trust.
- Proposed solution: Improve locator fallback for Office-derived chunks using sheet/table/row, slide number/title, heading path, or document section when available.
- Expected files touched: Office postprocessors, chunk/source-map generation, tests.
- Risk level: Medium. Touches conversion/chunk metadata and may require fixture updates.
- Validation method: Fixture tests for DOCX/PPTX/XLSX locator output; library smoke tests with `--has-locator`.
- v0.2.1 decision: Include only if scoped to one document family; otherwise defer.

### 6. Runner Usability Polish

- Problem: The chunked/resume runner works, but operational users may benefit from clearer progress summaries, exit codes, and final status output.
- Proposed solution: Add final summary fields such as expected unique manifests, total manifests, attempts, restarts, timeout count, and log paths. Keep runner behavior unchanged.
- Expected files touched: `scripts/Invoke-Office2MdChunkedConvert.ps1`, `docs/ops/cml125_batch_validation.md`, tests or dry-run checks if feasible.
- Risk level: Low to medium. PowerShell process handling should not be changed unless needed.
- Validation method: `-DryRun` checks for `-MaxFiles 3` and `-FullDirectory`; small max-files smoke if feasible.
- v0.2.1 decision: Include if docs-only or output-only; avoid process-control refactor.

### 7. CLI Usability Polish

- Problem: CLI help is accurate but some options are hard to discover, and Windows console rendering can mangle long option names or Unicode.
- Proposed solution: Improve help text, README examples, and possibly add clearer command descriptions. Avoid changing command signatures.
- Expected files touched: `office2md/cli.py`, README, tests only if help text is asserted.
- Risk level: Low.
- Validation method: CLI help snapshots by manual inspection; pytest/ruff.
- v0.2.1 decision: Include selectively.

## P3 Future / Optional Ideas

### 8. Legacy `.doc` Handling

- Problem: Full CML125 validation produced two failures from duplicate legacy `.doc` files.
- Proposed solution: Keep legacy `.doc` documented as unsupported/fragile for now. Later, evaluate optional LibreOffice-based preflight or conversion diagnostics.
- Expected files touched: converter routing, docs, tests with legacy fixtures if implemented later.
- Risk level: High if conversion behavior changes; low if docs-only.
- Validation method: Dedicated legacy Office fixture set and full regression pass.
- v0.2.1 decision: Defer. Keep as known limitation.

### 9. Optional Embedding / Vector Sidecar

- Problem: Some conceptual queries may benefit from semantic retrieval, but current FTS is practical and validated.
- Proposed solution: Keep as future-only design. If revisited, make it offline, optional, disabled by default, and sidecar-based.
- Expected files touched: future design docs first; later new embedding tables/sidecar files and CLI commands.
- Risk level: High. Adds dependencies, storage, model-selection, reproducibility, and validation burden.
- Validation method: Separate benchmark comparing FTS, token fallback, and hybrid search.
- v0.2.1 decision: Defer.

### 10. Office Image Export

- Problem: Office image references are counted but embedded Office images are not exported.
- Proposed solution: Future scoped feature for DOCX/PPTX image extraction and reference repair.
- Expected files touched: Office converters/postprocessors, assets handling, tests.
- Risk level: High. Changes output assets and Markdown references.
- Validation method: Office image fixture set and visual asset checks.
- v0.2.1 decision: Defer.

### 11. OCR

- Problem: Image-only or scanned content remains inaccessible without OCR.
- Proposed solution: Future explicit OCR controls and validation track.
- Expected files touched: conversion options, PDF/image pipeline, dependencies, docs, tests.
- Risk level: High. Adds dependency and quality variability.
- Validation method: OCR fixture set and explicit OCR usage reporting.
- v0.2.1 decision: Defer.

### 12. AI/MiniMax Enrichment

- Problem: Summaries and high-level entity enrichment could improve, but v0.2.0 intentionally validated a no-AI path.
- Proposed solution: Keep optional AI adapters out of the validated path. Revisit only as an opt-in future track.
- Expected files touched: AI adapter/docs/tests if resumed.
- Risk level: High for privacy, reproducibility, and validation.
- Validation method: Separate opt-in validation with AI disabled by default.
- v0.2.1 decision: Defer.

## Recommended First v0.2.1 Task

Start with query diagnostics.

Reason: it is low risk, does not change default results, and will make the remaining weak searches easier to analyze before changing ranking or aliases again.

Suggested order:

1. Add `search-library --diagnostics`.
2. Use diagnostics to review `vacuum pump fault` and `agitator temperature problem`.
3. Add only narrow ranking/alias improvements supported by diagnostics evidence.
4. Clean quality report formatting.
5. Add common workflow docs.

## Explicitly Deferred From v0.2.1

- embeddings/vector search
- OCR
- AI/MiniMax
- cloud/network dependency
- Office image export
- legacy `.doc` conversion
- broad synonym expansion
