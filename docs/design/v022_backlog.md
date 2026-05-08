# v0.2.2 Backlog

Baseline: `v0.2.1`

v0.2.1 is the current stable release. It completed the conservative v0.2.1 usability track on top of the validated v0.2.0 pipeline: search diagnostics, bounded token fallback candidate gathering, narrow fallback ranking polish, quality report wording, CLI help polish, and common workflow documentation.

v0.2.2 should remain a planning and polish release unless new validation reveals a real regression. The validated path must stay local and no-AI by default. Do not add embeddings/vector search, OCR, AI/MiniMax, cloud/network dependencies, Office image export, or legacy `.doc` conversion in v0.2.2.

## Baseline Validation

- Git status: clean on `master`
- HEAD/tag: `v0.2.1`
- Python: 3.11.9 from project `.venv`
- pytest: 67 passed
- ruff: all checks passed
- Current stable capabilities:
  - Office/PDF/text-like conversion
  - per-document Knowledge Pack output
  - Knowledge Library Builder
  - SQLite/FTS `library.db`
  - `library_index.json`
  - `library_graph.json`
  - Markdown portal
  - interop JSONL exports
  - `library-report`
  - `search-library`
  - `locate-document`
  - FTS ranking, token fallback, facets, filters, context, related chunks
  - alias/normalization
  - `search-library --diagnostics`
  - chunked/resume PowerShell runner
  - common workflow docs

## P0 Blockers

No P0 release blockers are currently identified for v0.2.2.

The v0.2.1 release is clean, tagged, and validated. v0.2.2 should not start by changing conversion behavior or search ranking. If a new CML125-style validation dataset exposes a regression, that regression should become the only P0 item and should be handled before any polish work.

## P1 Small High-Value Polish

### 1. Machine-Readable Search Diagnostics

- Problem: `search-library --diagnostics` is useful for humans, but the diagnostics are only printed as CLI tables. It is hard to compare queries across runs, save diagnostics evidence, or attach search diagnostics to validation reports.
- Proposed solution: Add an optional diagnostics export mode, such as `search-library --diagnostics --format json` or `--diagnostics-output diagnostics.json`, that serializes the existing diagnostics fields without changing default table output or search results.
- Expected files touched: `office2md/cli.py`, `office2md/library.py`, `tests/test_library_builder.py`, README, `docs/usage/common_workflows.md`.
- Risk level: Low. This should expose already computed diagnostics and must not change ranking or query behavior.
- Validation method: Unit test JSON diagnostics fields for FTS, alias, normalized query, token fallback, filters, and no-result cases. Manual smoke checks for `SY909735`, Chinese cooling water, `1THLS200`, `vacuum pump fault`, and `agitator temperature problem`.
- v0.2.2 decision: Include.

### 2. Search Result Export

- Problem: Search results are currently printed for interactive use. Operational users may need to save result sets for review, ticket evidence, validation comparisons, or handoff to downstream scripts without scraping Rich table output.
- Proposed solution: Add optional `search-library` result export for JSON or JSONL, for example `--output results.jsonl` or `--format json`. Include rank, chunk ID, document metadata, evidence type, locator, output directory, preview, mode, query used, alias/normalization metadata, matched tokens when available, and related chunks when requested.
- Expected files touched: `office2md/cli.py`, `office2md/library.py` only if result shaping needs a helper, `tests/test_library_builder.py`, README, `docs/usage/common_workflows.md`.
- Risk level: Low to medium. Low if implemented as pure output serialization; medium if CLI output modes are broadened too much.
- Validation method: Unit tests or CLI smoke tests confirming exported JSON/JSONL parses, preserves result count and ranking, includes diagnostics metadata, and works with `--facets`, `--context`, filters, and zero-result searches.
- v0.2.2 decision: Include, after diagnostics export.

### 3. Runner Final Summary Polish

- Problem: The chunked/resume PowerShell runner works, but final status review still requires reading logs and counting manifests in some cases. Operators need a concise final summary after long OneDrive-backed runs.
- Proposed solution: Add output-only final summary fields: supported files, expected unique manifests, actual manifest count, success count, failed count, skipped/existing count if available, attempts, restarts/timeouts, last command, and log directory. Avoid changing process-control behavior.
- Expected files touched: `scripts/Invoke-Office2MdChunkedConvert.ps1`, `docs/ops/cml125_batch_validation.md`, `docs/usage/common_workflows.md`.
- Risk level: Low to medium. Output-only changes are low risk; process tree or retry changes should be avoided in v0.2.2.
- Validation method: `-DryRun -MaxFiles 3`, `-DryRun -FullDirectory`, and a tiny max-files smoke run if practical. Confirm no input deletion, no behavior change to `--skip-existing`, and logs remain redirected.
- v0.2.2 decision: Include if kept output-only.

### 4. Office-Derived Locator Audit and One-Family Polish

- Problem: Some Office-derived chunks can still lack precise locators, which weakens trust in search results and `--has-locator` workflows.
- Proposed solution: First audit locator coverage by document family. Then choose exactly one low-risk family for v0.2.2, preferably XLSX/HMI or PPTX if the fixture coverage is already strong. Improve locator fallback using sheet/table/row, slide number/title, heading path, or section metadata already present in chunks and source maps.
- Expected files touched: one focused postprocessor in `office2md/postprocess/office_structure.py` or chunk/source-map generation helpers, `office2md/postprocess/knowledge_pack.py` if source-map fields need alignment, focused tests in `tests/test_office_enhancement.py` or `tests/test_library_builder.py`, README only if user-visible locator behavior changes.
- Risk level: Medium. Locator changes can alter chunk IDs, source maps, search filters, and fixture expectations if the scope is too broad.
- Validation method: Fixture tests for the chosen family; library smoke test with `--has-locator`; before/after counts for chunks without locators; ensure no change to conversion engines or Office image behavior.
- v0.2.2 decision: Include only after audit and only for one document family. Defer broad locator refactors.

## P2 Useful But Non-Urgent Improvements

### 5. Quality Report Detail Polish

- Problem: v0.2.1 improved key empty-state wording, but `_quality_report.md` can still be dense for larger libraries and does not clearly separate action items from informational metrics.
- Proposed solution: Refine report sections to group warnings, failed manifests, low-structure documents, page-level searchable PDFs, noisy chunks, chunks without locators, and HMI translation notes. Keep all metrics and scoring logic unchanged.
- Expected files touched: `office2md/library.py`, `tests/test_library_builder.py`, possibly README if report examples are added.
- Risk level: Low if formatting-only.
- Validation method: Unit tests for report text; rebuild a small fixture library; compare metrics before and after to confirm counts do not change.
- v0.2.2 decision: Include only if it stays formatting-only and does not displace P1 export work.

### 6. CLI Output Consistency Audit

- Problem: CLI commands are usable, but output conventions differ across `build-library`, `library-report`, `search-library`, and `locate-document`. This matters more if export modes are added.
- Proposed solution: Audit command help and output naming. Clarify option descriptions, keep positional syntax unchanged, and avoid introducing breaking aliases. Prefer documenting existing behavior over changing command contracts.
- Expected files touched: `office2md/cli.py`, README, `docs/usage/common_workflows.md`.
- Risk level: Low.
- Validation method: Manual help checks for `convert`, `build-library`, `search-library`, `locate-document`, and `library-report`; pytest and ruff.
- v0.2.2 decision: Include selectively.

### 7. Conservative Bilingual Alias Review

- Problem: v0.2.1 supports a small alias set for validated Chinese/HMI terms, but adding aliases without evidence can reduce search precision.
- Proposed solution: Review real query logs or manually collected validation queries. Add aliases only when there is clear CML125 evidence, exact terms are stable, and original exact matches remain unchanged.
- Expected files touched: `office2md/library.py`, `tests/test_library_builder.py`, README only if new examples are worth documenting.
- Risk level: Medium. Even small alias changes can alter fallback behavior and search expectations.
- Validation method: Before/after smoke set covering exact identifiers, existing bilingual aliases, weak operational queries, and no-hit identifiers such as `1THLS200`.
- v0.2.2 decision: Defer unless new evidence strongly justifies a specific alias.

### 8. Library Report Export

- Problem: `library-report` prints useful metrics but does not provide a direct JSON artifact for automation or release evidence.
- Proposed solution: Add optional report export, for example `library-report --format json` or `--output report.json`, using the existing `library_report()` dictionary.
- Expected files touched: `office2md/cli.py`, `tests/test_library_builder.py`, README or workflow docs.
- Risk level: Low.
- Validation method: JSON parse test, field presence test, and smoke check on a fixture library.
- v0.2.2 decision: Defer unless search export work finishes cleanly; this is a natural follow-up.

## P3 Deferred / Future Ideas

### 9. Legacy `.doc` Handling

- Problem: Full CML125 validation had two failed duplicate legacy `.doc` files, and legacy Office remains fragile.
- Proposed solution: Keep legacy `.doc` documented as unsupported/fragile. A future release may add preflight diagnostics or optional LibreOffice-specific handling, but v0.2.2 should not add legacy `.doc` conversion.
- Expected files touched: future converter routing, docs, tests with legacy fixtures.
- Risk level: High if conversion behavior changes.
- Validation method: Dedicated legacy Office fixture set and full regression pass.
- v0.2.2 decision: Defer.

### 10. Optional Embedding / Vector Sidecar

- Problem: Some broad conceptual queries may eventually benefit from semantic retrieval, but v0.2.1 search is already practical with FTS, fallback, facets, context, and diagnostics.
- Proposed solution: Keep as future-only design. If revisited, it must be offline, optional, disabled by default, sidecar-based, and benchmarked against current FTS before implementation.
- Expected files touched: future design docs first; later new optional sidecar outputs and CLI commands.
- Risk level: High due to dependencies, model choice, reproducibility, storage, validation, and user expectations.
- Validation method: Separate benchmark comparing FTS, token fallback, context, and any hybrid approach.
- v0.2.2 decision: Defer.

### 11. OCR

- Problem: Image-only or scanned files still require OCR for searchable text.
- Proposed solution: Keep OCR deferred. Any future OCR work should be explicit, opt-in, locally validated, and clearly reported in manifests.
- Expected files touched: future conversion options, PDF/image pipeline, dependencies, docs, and tests.
- Risk level: High due to dependency footprint and variable extraction quality.
- Validation method: Dedicated OCR fixture set with explicit `ocr_used` reporting.
- v0.2.2 decision: Defer.

### 12. AI/MiniMax Enrichment

- Problem: Summaries and semantic enrichment could be useful, but the validated path intentionally stays no-AI and local.
- Proposed solution: Keep AI/MiniMax out of v0.2.2. Existing opt-in adapter framework remains outside the validated default path.
- Expected files touched: future AI docs/tests only if a separate opt-in track is reopened.
- Risk level: High for privacy, reproducibility, validation, and operational governance.
- Validation method: Separate opt-in validation with AI disabled by default.
- v0.2.2 decision: Defer.

### 13. Office Image Export

- Problem: Office outputs record embedded image and missing asset counts, but embedded Office images are not exported.
- Proposed solution: Keep Office image export deferred. Future work needs a dedicated design for DOCX/PPTX asset extraction, Markdown reference repair, deduplication, and visual validation.
- Expected files touched: future Office postprocessors, asset handling, manifest fields, tests, docs.
- Risk level: High because output assets and Markdown references change.
- Validation method: Office image fixture set and visual asset checks.
- v0.2.2 decision: Defer.

### 14. Marker Integration Expansion

- Problem: Marker may improve some PDF outputs, but it adds dependency and validation complexity beyond the current stable no-AI path.
- Proposed solution: Keep Marker as optional/future. Do not change default routing or release validation around Marker in v0.2.2.
- Expected files touched: future converter routing, docs, tests.
- Risk level: Medium to high.
- Validation method: Dedicated PDF benchmark comparing Docling, MarkItDown fallback, and Marker.
- v0.2.2 decision: Defer.

## Recommended First v0.2.2 Task

Start with machine-readable search diagnostics.

Reason: it is low risk, builds directly on v0.2.1, does not change conversion, ranking, aliases, or default CLI behavior, and creates evidence that will make search result export and future query reviews easier to validate.

Suggested order:

1. Add machine-readable diagnostics export.
2. Add search result export using the same output conventions.
3. Add output-only runner final summary polish.
4. Audit Office-derived locator coverage and choose at most one document family for scoped locator polish.
5. Apply formatting-only quality report and CLI consistency polish if time remains.

## Explicitly Deferred From v0.2.2

- embeddings/vector search
- OCR
- AI/MiniMax
- cloud/network dependency
- Office image export
- legacy `.doc` conversion
- broad synonym expansion
- broad Office locator refactor
- search ranking changes not backed by new diagnostics evidence
- conversion engine routing changes
