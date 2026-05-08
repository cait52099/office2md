# Phase 3.2 Field Validation Plan

Status: validation and evidence generation only.

Baseline release: `v0.2.4`.

## Purpose

Phase 3.2 validates the current stable office2md workflow against the existing full CML125 library and source tree. The goal is to produce reproducible evidence for real-use readiness, search usefulness, reporting clarity, and runner dry-run behavior without changing code or conversion/search behavior.

## Validation Scope

In scope:

- Confirm the repository baseline is clean and tagged `v0.2.4`.
- Run the existing test and lint suite.
- Generate machine-readable library-report and search evidence with the v0.2.4 CLI.
- Capture locate-document evidence for common CML125 lookups.
- Capture chunked/resume runner `-MaxFiles 3 -DryRun` output.
- Summarize evidence into a field validation report.

Out of scope:

- Code changes.
- New tags.
- Search core, ranking, alias, token fallback, conversion, runner process-control, report scoring, or Office locator behavior changes.
- Embeddings/vector search, OCR, AI/MiniMax, cloud/network dependencies, Office image export, or legacy `.doc` conversion.

## Inputs

Library path:

```text
C:\Users\hcai\OneDrive - The Estée Lauder Companies Inc\Desktop\Symex_CML125_library_full
```

Source path:

```text
C:\Users\hcai\OneDrive - The Estée Lauder Companies Inc\Desktop\Symex\CML125
```

Evidence output folder:

```text
C:\Users\hcai\OneDrive - The Estée Lauder Companies Inc\Desktop\office2md_phase32_cml125_evidence
```

## Query List

- `SY909735`
- `Translation`
- `CML125`
- `vacuum pump fault`
- `agitator temperature problem`
- `cooling water`
- `冷却水`
- `alarm history`
- `报警历史`
- `seal liquid`
- `密封液`
- `operation manual`
- `操作手册`
- `temperature probe`
- `CIP`
- `1V2005`
- `2M2001`
- `1THLS200`
- `S7-300`

## Evidence Files

Library report:

- `library_report.json`

Search exports:

- `search_sy909735.json`
- `search_translation.json`
- `search_vacuum_pump_fault.json`
- `search_agitator_temperature_problem.json`
- `search_cooling_water.json`
- `search_chinese_cooling_water.json`
- `search_alarm_history.json`
- `search_seal_liquid.json`
- `search_operation_manual.json`
- `search_temperature_probe.json`
- `search_cip.json`
- `search_1v2005.json`
- `search_2m2001.json`
- `search_1thls200.json`
- `search_s7_300.json`

Locate-document evidence:

- `locate_sy909735.txt`
- `locate_translation.txt`

Runner dry-run evidence:

- `runner_dryrun_maxfiles3.txt`

## Success Criteria

- Git status is clean at baseline and HEAD is tagged `v0.2.4`.
- `python -m pytest` passes in the project virtual environment.
- `python -m ruff check .` passes in the project virtual environment.
- `library_report.json` is created and includes CML125 counts, quality metrics, and missing-locator detail.
- Search export files are created as UTF-8 JSON and include query metadata, diagnostics summary, result counts, and result summaries.
- Locate-document evidence files are created for `SY909735` and `Translation`.
- Runner dry-run evidence records supported files, expected unique manifests, attempts used, and final status.
- The validation report classifies each query as useful, partial, or no.

## Decision Gate

Use the validation report to choose one of:

- Continue real use: evidence supports day-to-day CML125 lookup and reporting with no immediate release work.
- Create v0.2.5 bugfix/polish: evidence shows small local/reporting/docs issues that should be fixed before broader use.
- Start v0.3.0 planning: evidence shows the current local workflow is stable enough and next work should be larger-scope planning.
- Pause development: evidence shows validation blockers, environment instability, or workflow mismatch that should be resolved before more features.
