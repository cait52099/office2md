# Phase 3.2 CML125 Field Validation Report

Status: validation and evidence generation only.

Evidence folder:

```text
C:\Users\hcai\OneDrive - The Estée Lauder Companies Inc\Desktop\office2md_phase32_cml125_evidence
```

## Baseline

- Repository path: `C:\Users\hcai\Downloads\office2md`
- Git baseline: `v0.2.4`
- Working tree at baseline: clean
- Library path: `C:\Users\hcai\OneDrive - The Estée Lauder Companies Inc\Desktop\Symex_CML125_library_full`
- Source path: `C:\Users\hcai\OneDrive - The Estée Lauder Companies Inc\Desktop\Symex\CML125`

Validation commands used the project virtual environment Python 3.11.9.

## Test And Lint

```text
python -m pytest
71 passed

python -m ruff check .
All checks passed
```

## Evidence Files Generated

Library/report evidence:

- `library_report.json`
- `library_report_console.txt`

Search evidence:

- `search_sy909735.json`
- `search_translation.json`
- `search_cml125.json`
- `search_vacuum_pump_fault.json`
- `search_agitator_temperature_problem.json`
- `search_cooling_water.json`
- `search_chinese_cooling_water.json`
- `search_alarm_history.json`
- `search_chinese_alarm_history.json`
- `search_seal_liquid.json`
- `search_chinese_seal_liquid.json`
- `search_operation_manual.json`
- `search_chinese_operation_manual.json`
- `search_temperature_probe.json`
- `search_cip.json`
- `search_1v2005.json`
- `search_2m2001.json`
- `search_1thls200.json`
- `search_s7_300.json`

Console captures were also written for each search JSON file using the `_console.txt` suffix.

Locate-document evidence:

- `locate_sy909735.txt`
- `locate_translation.txt`

Runner evidence:

- `runner_dryrun_maxfiles3.txt`

Note: the original requested search export filename list omitted `CML125`, `报警历史`, `密封液`, and `操作手册`, while the query list included them. Extra search JSON files were generated for those four queries so the validation report covers the full query list.

## Library Report Key Metrics

| Metric | Value |
| --- | ---: |
| documents_count | 587 |
| chunks_count | 4238 |
| entities_count | 365 |
| noisy_chunks_count | 0 |
| chunks_without_locator | 462 |
| low_quality_documents | 85 |
| page_level_pdf_documents | 493 |

Locator detail from `library_report.json`:

- `chunks_without_locator_by_document_kind`: `document: 462`
- `chunks_without_locator_by_evidence_type`: `text: 462`
- `chunks_without_locator_by_extension`: `docx: 457`, `xlsx: 3`, `pptx: 2`
- Top source: `Symex CML125 Purchase Agreement_0405.docx`, 227 chunks without locator

## Query Result Summary

| Query | Mode | Result Count | Top Document | Top Kind | Locator Present | Useful | Notes |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| `SY909735` | `fts` | 104 | `Copy of SY909735_Translation_Chinese ver.1` | `hmi_translation_xlsx` | yes | yes | Identifier lookup returns direct CML125/HMI hits. |
| `Translation` | `fts` | 52 | `Copy of SY909735_Translation_Chinese ver.1` | `hmi_translation_xlsx` | yes | yes | Translation document family is found directly. |
| `CML125` | `fts` | 35 | `Equipment list` | `generic_pdf` | yes | yes | Project identifier returns CML125 equipment/library hits. |
| `vacuum pump fault` | `token_fallback` | 321 | `Faults and measures catalog_SY909735_AH` | `fault_catalog_pdf` | yes | yes | Top result is fault-catalog evidence. |
| `agitator temperature problem` | `token_fallback` | 322 | `Faults and measures catalog_SY909735_AH` | `fault_catalog_pdf` | yes | yes | Top result is fault-catalog evidence. |
| `cooling water` | `fts` | 32 | `Copy of SY909735_Translation_Chinese ver.1` | `hmi_translation_xlsx` | yes | yes | Cooling-water query returns HMI/CML125 evidence. |
| `冷却水` | `fts` | 32 | `Copy of SY909735_Translation_Chinese ver.1` | `hmi_translation_xlsx` | yes | yes | Chinese cooling-water query returns the expected HMI family. |
| `alarm history` | `token_fallback` | 37 | `Copy of SY909735_Translation_Chinese ver.1` | `hmi_translation_xlsx` | yes | yes | Alarm-history query returns HMI translation evidence. |
| `报警历史` | `fts` | 30 | `Copy of SY909735_Translation_Chinese ver.1` | `hmi_translation_xlsx` | yes | yes | Chinese alarm-history query returns the expected HMI family. |
| `seal liquid` | `token_fallback` | 237 | `Copy of SY909735_Translation_Chinese ver.1` | `hmi_translation_xlsx` | yes | yes | Seal-liquid query returns matching HMI/technical evidence. |
| `密封液` | `fts` | 23 | `Copy of SY909735_Translation_Chinese ver.1` | `hmi_translation_xlsx` | yes | yes | Chinese seal-liquid query returns the expected HMI family. |
| `operation manual` | `fts` | 7 | `Operating instructions pump` | `manual_pdf` | yes | yes | Operation manual query returns manual evidence. |
| `操作手册` | `fts` | 7 | `Operating instructions pump` | `manual_pdf` | yes | yes | Chinese operation-manual query returns manual evidence. |
| `temperature probe` | `fts` | 20 | `Copy of SY909735_Translation_Chinese ver.1` | `hmi_translation_xlsx` | yes | yes | Temperature-probe query returns CML125/HMI evidence. |
| `CIP` | `fts` | 222 | `Copy of SY909735_Translation_Chinese ver.1` | `hmi_translation_xlsx` | yes | yes | CIP query returns HMI/library evidence. |
| `1V2005` | `fts` | 5 | `Copy of SY909735_Translation_Chinese ver.1` | `hmi_translation_xlsx` | yes | yes | Exact part/equipment lookup returns hits. |
| `2M2001` | `fts` | 2 | `Copy of SY909735_Translation_Chinese ver.1` | `hmi_translation_xlsx` | yes | yes | Exact part/equipment lookup returns hits. |
| `1THLS200` | `fts` | 7 | `Copy of SY909735_Translation_Chinese ver.1` | `hmi_translation_xlsx` | yes | yes | Exact identifier lookup returns hits. |
| `S7-300` | `fts` | 62 | `Content` | `datasheet_pdf` | yes | yes | Siemens/controller query returns datasheet evidence. |

## Runner Dry-Run Summary

From `runner_dryrun_maxfiles3.txt`:

| Field | Value |
| --- | ---: |
| supported files | 598 |
| expected unique manifests | 3 |
| attempts used | 0 |
| final status | `dry-run` |

The dry run did not start conversion and did not alter conversion behavior.

## Issues Found

No release-blocking issues were found in Phase 3.2 field validation.

Observations:

- Broad natural-language queries can return many results, but the top results are useful for the tested CML125 workflow.
- Some queries rely on `token_fallback`, especially failure-intent phrases such as `vacuum pump fault` and `agitator temperature problem`; this is expected current behavior.
- The current full library still has 462 chunks without locators, dominated by generic Office raw-markdown DOCX chunks. This is already documented in v0.2.4 reporting and is not a library-builder data-loss issue.
- For Windows console display of Chinese query text, keep `$env:PYTHONIOENCODING = "utf-8"` and `$env:PYTHONUTF8 = "1"` set before smoke tests.

## Recommendation

Recommendation: **continue real use**.

Rationale:

- Test and lint are clean.
- Library report metrics match the expected v0.2.4 CML125 baseline.
- Search and locate-document evidence covers the requested English, Chinese, identifier, fault, and equipment queries.
- Runner dry-run evidence confirms safe operational command shape and expected counts.
- No validation blocker requires v0.2.5 before real use.

Potential next planning:

- Use real-user feedback from Phase 3.2 to decide whether v0.2.5 should be a small bugfix/polish release.
- If field use remains stable, begin v0.3.0 planning around larger workflow needs rather than changing search/conversion behavior immediately.
