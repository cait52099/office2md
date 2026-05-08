# office2md Common Workflows

These examples use the current positional CLI syntax:

- `convert INPUT_PATH OUTPUT [OPTIONS]`
- `build-library INPUT_DIR OUTPUT_DIR`

PowerShell users can set UTF-8 output before search/report smoke tests:

```powershell
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
```

The validated default path does not use OCR, AI/MiniMax, embeddings/vector search, cloud services, or Office image export.

## Single Document Conversion

```powershell
.\.venv\Scripts\python.exe -m office2md.cli convert `
  "C:\path\input.pdf" `
  "C:\path\office2md_output" `
  --engine auto `
  --profile kb `
  --render-pdf-pages `
  --max-render-pages 3 `
  --max-text-pages 10 `
  --no-force-ocr `
  --no-use-ai `
  --ai-backend none
```

## Directory Conversion

```powershell
.\.venv\Scripts\python.exe -m office2md.cli convert `
  "C:\path\input_dir" `
  "C:\path\office2md_output" `
  --recursive `
  --engine auto `
  --profile kb `
  --render-pdf-pages `
  --max-render-pages 3 `
  --max-text-pages 10 `
  --no-force-ocr `
  --no-use-ai `
  --ai-backend none
```

For a first pass, add `--max-files 20` or `--dry-run`.

## Build A Knowledge Library

```powershell
.\.venv\Scripts\python.exe -m office2md.cli build-library `
  "C:\path\office2md_output" `
  "C:\path\office2md_library"
```

## Run Library Report

```powershell
.\.venv\Scripts\python.exe -m office2md.cli library-report `
  "C:\path\office2md_library"
```

Export the same report metrics to UTF-8 JSON. Parent directories are created automatically:

```powershell
.\.venv\Scripts\python.exe -m office2md.cli library-report `
  "C:\path\office2md_library" `
  --export-json "C:\path\exports\library_report.json"
```

## Search Examples

Basic search:

```powershell
.\.venv\Scripts\python.exe -m office2md.cli search-library `
  "C:\path\office2md_library" `
  "SY909735" `
  --limit 10
```

Diagnostics:

```powershell
.\.venv\Scripts\python.exe -m office2md.cli search-library `
  "C:\path\office2md_library" `
  "vacuum pump fault" `
  --limit 10 `
  --diagnostics
```

Machine-readable diagnostics JSON is appended after the normal tables:

```powershell
.\.venv\Scripts\python.exe -m office2md.cli search-library `
  "C:\path\office2md_library" `
  "vacuum pump fault" `
  --limit 10 `
  --diagnostics-json
```

Export search results to UTF-8 JSON. Parent directories are created automatically:

```powershell
.\.venv\Scripts\python.exe -m office2md.cli search-library `
  "C:\path\office2md_library" `
  "SY909735" `
  --limit 20 `
  --export-json "C:\path\exports\search_results_sy909735.json"
```

Facets:

```powershell
.\.venv\Scripts\python.exe -m office2md.cli search-library `
  "C:\path\office2md_library" `
  "CIP" `
  --facets `
  --limit 20
```

Nearby context. `--context` requires an integer argument:

```powershell
.\.venv\Scripts\python.exe -m office2md.cli search-library `
  "C:\path\office2md_library" `
  "alarm history" `
  --context 2 `
  --limit 5
```

Filter by output directory:

```powershell
.\.venv\Scripts\python.exe -m office2md.cli search-library `
  "C:\path\office2md_library" `
  "PLC" `
  --output-dir copy-of-sy909735-translation-chinese-ver-1 `
  --limit 10
```

Filter by entity:

```powershell
.\.venv\Scripts\python.exe -m office2md.cli search-library `
  "C:\path\office2md_library" `
  "pump" `
  --entity HMI `
  --limit 10
```

## Locate Documents

```powershell
.\.venv\Scripts\python.exe -m office2md.cli locate-document `
  "C:\path\office2md_library" `
  "Translation"

.\.venv\Scripts\python.exe -m office2md.cli locate-document `
  "C:\path\office2md_library\library.db" `
  "SY909735"
```

## CML125 / OneDrive Full-Directory Workflow

Large OneDrive-backed directories may stall while files hydrate or while external converters process difficult files. Use the chunked/resume runner for full-directory validation:

```powershell
.\scripts\Invoke-Office2MdChunkedConvert.ps1 `
  -InputPath "C:\path\OneDrive\Desktop\Symex\CML125" `
  -OutputPath "C:\path\Desktop\Symex_CML125_validation_full" `
  -LogDirectory "C:\path\Desktop\Symex_CML125_validation_full_logs" `
  -FullDirectory `
  -TimeoutMinutes 45 `
  -MaxAttempts 30
```

Then build and report the library:

```powershell
.\.venv\Scripts\python.exe -m office2md.cli build-library `
  "C:\path\Desktop\Symex_CML125_validation_full" `
  "C:\path\Desktop\Symex_CML125_library_full"

.\.venv\Scripts\python.exe -m office2md.cli library-report `
  "C:\path\Desktop\Symex_CML125_library_full"
```

The runner uses `--skip-existing`, redirects logs, monitors expected unique manifest outputs, and restarts only its own launched conversion process tree.
