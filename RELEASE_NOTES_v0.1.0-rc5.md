# office2md v0.1.0-rc5 Release Notes

Release candidate focused on Phase 2.9A, 2.9A.1, and 2.9A.2 Office Knowledge Pack enhancement. The release improves Office outputs for knowledge-base ingestion and human review while keeping the core path local and no-AI.

## Office Knowledge Pack Enhancement

Office files are still converted through MarkItDown, then office2md adds structured Knowledge Pack output on top of the raw Markdown:

- DOCX/PPTX/XLSX-specific `document_kind` classification.
- Office metadata extraction into `knowledge.json`.
- Office entities into `entities.json`.
- Retrieval provenance in `chunks.jsonl` and `source_map.json`.
- Embedded and missing Office image statistics and manifest warnings without exporting Office images.

Validated Office document kinds:

- `process_development_presentation`
- `release_rationale_docx`
- `mpdp_table_xlsx`

## PPTX Process-Development Reconstruction

Process-development / scale-up evidence decks now get knowledge-facing structure before the raw slide content in `document.md`:

- `Presentation Summary`
- `Key Project Metadata`
- `Slide Index`
- `Topic Outline`
- `Process Development Narrative`
- `Batch Study Summary`
- `Slides` with slide-level source, topic label, visual evidence flag, and raw slide text

PPTX chunks and source maps preserve slide-level provenance:

- `evidence_type: slide`
- `slide_number`
- `slide_title`
- `topic_label`
- `locator: Slide N`
- `visual_evidence_needed`

## Batch Study Summary Accuracy

Phase 2.9A.2 improves batch evidence extraction for process-development PPTX decks:

- `batch_study_summary[]` now includes `confidence`, `evidence_slides`, `evidence_snippet`, and `locators`.
- Batch summaries retain multiple evidence slides instead of collapsing to a single locator.
- Result status is only assigned when the batch and result are in the same table row or a close evidence block.
- Generic risk-assessment text is no longer allowed to overwrite specific batch outcomes.

Validated corrections on `43DS-LS Daily Rescue Eye Serum 20260417.pptx`:

- `VL322673` is corrected to `Shake stability fail`, not `pass`.
- `VL324017` is corrected to `Success` and keeps evidence including Slide 20, Slide 22, and Slide 23.
- `VL325458` remains `Fail`.
- `VL325459` keeps `F/TH fail` with Slide 33 evidence.
- `VL326528` keeps `100kg`, `Symex + M4E`, and `25L/min` evidence while avoiding unsupported result inference.

## Topic Label Polish

PPTX topic labels were tightened for retrieval:

- Slide 14 `Feasibility study for Pilot Scale-up` is classified as `Batch / Pilot History`, not `Micro / Risk Assessment`.
- `Micro / Risk Assessment` remains reserved for micro issue and formula technical risk assessment content.

## DOCX Release Rationale Polish

Release rationale DOCX outputs now include knowledge-facing sections before raw content:

- `Release Summary`
- `Key Release Metadata`
- `Key Process Parameters`
- `Recommendation`

Extracted metadata includes project number, product name, mass codes, manufacturing/filling locations, formula system, specialty equipment, process parameters, viscosity adjustment, and recommendation when present.

## XLSX Phase-Level Provenance

MPDP / scale-up XLSX outputs now retain table provenance and add phase-level chunks:

- `evidence_type: table`
- `evidence_type: table_section`
- PFA / Pilot / Practice / Pre-Production / Production phase chunks
- sheet/table provenance in `source_map.json`

## Operation Manual Cleanup

Operation Manual PDF outputs keep rc4 section-aware behavior and add semantic title cleanup:

- Wiring-diagram-only semantic titles such as `Cable Overview`, `Power Supply`, and `Cover Sheet` are not assigned to manual source maps.
- Manual `section_outline` entries with page hints beyond `pages_count` are filtered.

## Asset Handling

Office image export is intentionally deferred to Phase 2.9B.

rc5 only records:

- `embedded_images_count`
- `missing_assets_count`
- manifest warnings for counted-but-not-exported embedded Office images
- manifest warnings for Markdown image references that do not map to extracted assets

## Validation

Real 5-file validation covered:

- `43DS MPDP.xlsx`
- `43DS-LS Daily Rescue Eye Serum 20260417.pptx`
- `43DS-00-M01U PPPBC release rational.docx`
- `Operation manual EN.pdf`
- `SY909735_Wiring diagram_Revision B_19_06_2019.pdf`

Validation highlights:

- PPTX: `slide: 33`, `topic: 9`, `batch_study: 11`
- XLSX: `table: 1`, `table_section: 5`
- DOCX: required release rationale sections present
- Operation Manual: no wiring-only semantic title noise in manual source map
- Wiring Diagram: drawing index preserved

## Test Status

```bash
python -m pytest -q
54 passed

python -m ruff check office2md tests
All checks passed!
```

## No-AI Core Path

rc5 remains a local, no-AI release candidate:

- No AI API.
- No MiniMax dependency.
- No OCR.
- No Marker.
- No real Office image extraction.

AI remains optional and disabled by default.

## Suggested Local Git Commands

If this directory should become a local git release:

```bash
git init
git add .
git commit -m "Release v0.1.0-rc5"
git tag v0.1.0-rc5
```
