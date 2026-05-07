# CML125 Batch Validation Runner

Phase 3.0.5a showed that large CML125 conversions can stall during long PDF batches even when the final conversion is recoverable with `--skip-existing`.

Observed stalls:

- after 103 outputs at `Pfannenberg_PF_66.000_EGCon.pdf`
- after 203 outputs at `Rittal_SV9340.000_man.int.pdf`

Both runs resumed successfully by restarting `convert` with `--skip-existing`. The operational runner in `scripts/Invoke-Office2MdChunkedConvert.ps1` automates that pattern.

## When To Use

Use the runner for CML125 300-file, 500-file, and full-directory validation runs where a single long `convert` process may stall or exceed the tool/session timeout.

The runner does not change conversion logic. It repeatedly starts:

```powershell
python -m office2md.cli convert INPUT OUTPUT --recursive --engine auto --profile kb --render-pdf-pages --max-render-pages 3 --max-text-pages 10 --no-force-ocr --no-use-ai --ai-backend none --skip-existing
```

It redirects stdout and stderr to timestamped logs, checks generated `manifest.json` files against expected output folders, stops a timed-out process tree, and restarts until the expected unique manifest count is reached. The expected count can be lower than the scanner-supported file count when duplicate source files map to the same output folder.

## 300-File Example

```powershell
cd C:\Users\hcai\Downloads\office2md
$env:PYTHONIOENCODING="utf-8"
$env:PYTHONUTF8="1"

.\scripts\Invoke-Office2MdChunkedConvert.ps1 `
  -InputPath "C:\Users\hcai\OneDrive - The Estée Lauder Companies Inc\Desktop\Symex\CML125" `
  -OutputPath "C:\Users\hcai\OneDrive - The Estée Lauder Companies Inc\Desktop\Symex_CML125_validation_300" `
  -LogDirectory "C:\Users\hcai\OneDrive - The Estée Lauder Companies Inc\Desktop\Symex_CML125_validation_300_logs" `
  -MaxFiles 300 `
  -TimeoutMinutes 45 `
  -MaxAttempts 10
```

Then build and report:

```powershell
.\.venv\Scripts\python.exe -m office2md.cli build-library `
  "C:\Users\hcai\OneDrive - The Estée Lauder Companies Inc\Desktop\Symex_CML125_validation_300" `
  "C:\Users\hcai\OneDrive - The Estée Lauder Companies Inc\Desktop\Symex_CML125_library_300"

.\.venv\Scripts\python.exe -m office2md.cli library-report `
  "C:\Users\hcai\OneDrive - The Estée Lauder Companies Inc\Desktop\Symex_CML125_library_300"
```

## Full-Directory Example

Use `-FullDirectory` instead of `-MaxFiles`. The runner counts scanner-supported files and expected unique output manifests before starting.

```powershell
cd C:\Users\hcai\Downloads\office2md
$env:PYTHONIOENCODING="utf-8"
$env:PYTHONUTF8="1"

.\scripts\Invoke-Office2MdChunkedConvert.ps1 `
  -InputPath "C:\Users\hcai\OneDrive - The Estée Lauder Companies Inc\Desktop\Symex\CML125" `
  -OutputPath "C:\Users\hcai\OneDrive - The Estée Lauder Companies Inc\Desktop\Symex_CML125_validation_full" `
  -LogDirectory "C:\Users\hcai\OneDrive - The Estée Lauder Companies Inc\Desktop\Symex_CML125_validation_full_logs" `
  -FullDirectory `
  -TimeoutMinutes 45 `
  -MaxAttempts 30
```

## Dry Run

Use `-DryRun` to confirm paths, supported file count, expected unique manifest count, and the exact command without starting conversion.

```powershell
.\scripts\Invoke-Office2MdChunkedConvert.ps1 `
  -InputPath "C:\Users\hcai\OneDrive - The Estée Lauder Companies Inc\Desktop\Symex\CML125" `
  -OutputPath "C:\Users\hcai\OneDrive - The Estée Lauder Companies Inc\Desktop\Symex_CML125_validation_300" `
  -MaxFiles 300 `
  -DryRun
```

## OneDrive Risk

CML125 lives under OneDrive. On-demand file hydration, sync locking, and reparse/recall attributes can slow or stall conversion of large PDFs. If a run repeatedly stalls on the same file, first check whether the source tree is fully available offline before treating it as a converter bug.

## Notes

- Office temporary files whose names start with `~$` are skipped by the scanner.
- The runner stops when the expected output folders contain `manifest.json`, not based on raw scanner-supported source file count.
- Legacy `.doc` files can fail as unsupported input. Phase 3.0 keeps these documented as known unsupported files unless a later requirement demands legacy Word conversion.
- Keep OCR, AI, embedding/vector search, and Office image export disabled for Phase 3.0 validation.
