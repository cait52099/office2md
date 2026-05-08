# office2md Demo Evidence Package

This package gives copy-paste PowerShell commands for validating the current local office2md library workflow after v0.2.3-rc1.

It assumes an existing built CML125 library:

```powershell
$ProjectRoot = "C:\Users\hcai\Downloads\office2md"
$LibraryPath = "C:\Users\hcai\OneDrive - The Estée Lauder Companies Inc\Desktop\Symex_CML125_library_full"
$SourcePath = "C:\Users\hcai\OneDrive - The Estée Lauder Companies Inc\Desktop\Symex\CML125"
$EvidenceDir = "C:\Users\hcai\OneDrive - The Estée Lauder Companies Inc\Desktop\office2md_demo_evidence"
```

Paths with spaces must stay quoted. The validated default workflow does not use OCR, AI/MiniMax, embeddings/vector search, cloud services, or Office image export. Legacy `.doc` remains unsupported or fragile and should stay tracked as known unsupported input unless a later release explicitly adds that conversion path.

## 1. Environment Check

```powershell
cd $ProjectRoot
.\.venv\Scripts\Activate.ps1
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

python --version
python -m pytest
python -m ruff check .
```

Expected reference for v0.2.3-rc1:

- Python 3.11.x in the project virtual environment.
- `python -m pytest` reports `70 passed`.
- `python -m ruff check .` reports all checks passed.

## 2. Library Report

Print the normal report table:

```powershell
python -m office2md.cli library-report $LibraryPath
```

Export the same report metrics to UTF-8 pretty JSON. Parent directories are created automatically:

```powershell
python -m office2md.cli library-report `
  $LibraryPath `
  --export-json "$EvidenceDir\library_report.json"
```

Expected CML125 reference evidence:

- `documents_count`: 587
- `chunks_count`: 4238
- `entities_count`: 365
- `noisy_chunks_count`: 0
- `low_quality_documents`: 85
- `page_level_pdf_documents`: 493

The export command should still print the normal report table and then print:

```text
export_json: <path>
```

## 3. Search Diagnostics

Machine-readable diagnostics JSON is appended after normal search output.

```powershell
python -m office2md.cli search-library `
  $LibraryPath `
  "SY909735" `
  --limit 3 `
  --diagnostics-json

python -m office2md.cli search-library `
  $LibraryPath `
  "冷却水" `
  --limit 3 `
  --diagnostics-json

python -m office2md.cli search-library `
  $LibraryPath `
  "vacuum pump fault" `
  --limit 3 `
  --diagnostics-json
```

The diagnostics JSON includes query metadata, mode, alias/normalization metadata, token fallback status, filters, result counts, evidence/document-kind summaries, locator coverage, hints, and compact result summaries.

## 4. Search Export

Export compact search results to UTF-8 pretty JSON:

```powershell
python -m office2md.cli search-library `
  $LibraryPath `
  "vacuum pump fault" `
  --limit 3 `
  --export-json "$EvidenceDir\search_vacuum_pump_fault.json"
```

Export search results while also printing diagnostics, facets, nearby context, and diagnostics JSON. `--context` requires an integer argument:

```powershell
python -m office2md.cli search-library `
  $LibraryPath `
  "vacuum pump fault" `
  --limit 3 `
  --diagnostics `
  --facets `
  --context 2 `
  --diagnostics-json `
  --export-json "$EvidenceDir\search_vacuum_pump_fault_context.json"
```

When `--export-json` and `--diagnostics-json` are combined, the export confirmation prints during normal output and the diagnostics JSON remains last.

## 5. Locate Document

```powershell
python -m office2md.cli locate-document `
  $LibraryPath `
  "SY909735"

python -m office2md.cli locate-document `
  $LibraryPath `
  "Translation"
```

Use `locate-document` when a search result points to a document family and you need the source file, output directory, or library document quickly.

## 6. Runner Dry Run

Use a dry run to verify runner paths, counts, and final summary without starting conversion:

```powershell
.\scripts\Invoke-Office2MdChunkedConvert.ps1 `
  -InputPath $SourcePath `
  -OutputPath "$EvidenceDir\runner_dry_run_output" `
  -LogDirectory "$EvidenceDir\runner_dry_run_logs" `
  -MaxFiles 3 `
  -DryRun
```

Expected dry-run final summary fields include:

- input path
- output path
- log directory
- mode: `MaxFiles`
- supported file count
- expected unique manifest count
- final manifest count
- completed expected manifest count
- failed manifest count
- attempts used
- timeout/restart count
- max attempts
- timeout minutes
- target reached
- final status: `dry-run`
- log location
- recommended `build-library` command

Expected CML125 runner reference evidence:

- supported files: 598
- expected unique manifests for full directory: 588
- expected unique manifests for `-MaxFiles 3`: 3
- attempts used in dry run: 0

## 7. Notes

- Set `$env:PYTHONIOENCODING = "utf-8"` and `$env:PYTHONUTF8 = "1"` before bilingual search smoke tests.
- Quote every path that contains spaces.
- `--context` and `--related` require integer arguments.
- The default validated path does not use OCR, AI/MiniMax, embeddings/vector search, cloud services, or Office image export.
- Legacy `.doc` remains unsupported or fragile in the validated path.
- Search diagnostics/export and library-report export are local deterministic artifacts for review, scripting, and release evidence.
