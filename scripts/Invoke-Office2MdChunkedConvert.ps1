param(
    [Parameter(Mandatory = $true)]
    [string]$InputPath,

    [Parameter(Mandatory = $true)]
    [string]$OutputPath,

    [string]$Python = ".\.venv\Scripts\python.exe",

    [string]$LogDirectory = "",

    [int]$MaxFiles = 0,

    [int]$TimeoutMinutes = 45,

    [int]$MaxAttempts = 20,

    [switch]$FullDirectory,

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Resolve-Office2MdPath {
    param([string]$PathValue)
    if ([System.IO.Path]::IsPathRooted($PathValue)) {
        return $PathValue
    }
    return (Join-Path (Get-Location) $PathValue)
}

function Get-ExpectedManifestCount {
    param(
        [string]$PythonPath,
        [string]$RootPath,
        [string]$OutputRootPath,
        [int]$MaxFileCount
    )
    $code = @'
from pathlib import Path
import sys
from slugify import slugify
from office2md.detector import sha256_file
from office2md.scanner import scan_input

source_root = Path(sys.argv[1])
output_root = Path(sys.argv[2])
max_file_count = int(sys.argv[3])
files = scan_input(source_root, recursive=True)
selected_files = files[:max_file_count] if max_file_count > 0 else files
seen = {}
targets = []
for source in selected_files:
    checksum = sha256_file(source)
    slug = slugify(source.stem) or "document"
    base_target = output_root / slug
    source_key = (str(source.resolve()), checksum)
    if base_target not in seen:
        target = base_target
    elif seen[base_target] == source_key:
        target = base_target
    else:
        short_hash = checksum.split(":", 1)[-1][:8]
        target = output_root / f"{slug}-{short_hash}"
    seen[target] = source_key
    targets.append(target)
print(len(files))
print(len(set(targets)))
for target in sorted({target.name for target in targets}):
    print(target)
'@
    $encodedCode = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($code))
    $bootstrap = "import base64; exec(base64.b64decode('$encodedCode').decode('utf-8'))"
    $output = & $PythonPath -c $bootstrap $RootPath $OutputRootPath $MaxFileCount
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to count expected manifests with office2md.scanner."
    }
    return @{
        Supported = [int]($output | Select-Object -First 1)
        Expected = [int]($output | Select-Object -Skip 1 -First 1)
        Names = [string[]]($output | Select-Object -Skip 2)
    }
}

function Get-ManifestCount {
    param([string]$RootPath)
    if (-not (Test-Path -LiteralPath $RootPath)) {
        return 0
    }
    return (Get-ChildItem -LiteralPath $RootPath -Recurse -Filter manifest.json -File -ErrorAction SilentlyContinue | Measure-Object).Count
}

function Get-FailedManifestCount {
    param([string]$RootPath)
    if (-not (Test-Path -LiteralPath $RootPath)) {
        return 0
    }
    $failed = 0
    $manifests = Get-ChildItem -LiteralPath $RootPath -Recurse -Filter manifest.json -File -ErrorAction SilentlyContinue
    foreach ($manifest in $manifests) {
        try {
            $data = Get-Content -LiteralPath $manifest.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($data.status -eq "failed") {
                $failed += 1
            }
        } catch {
            # Keep the summary best-effort; unreadable manifests are still counted by Get-ManifestCount.
        }
    }
    return $failed
}

function Get-ExpectedManifestPresentCount {
    param(
        [string]$RootPath,
        [string[]]$ExpectedNames
    )
    if (-not (Test-Path -LiteralPath $RootPath)) {
        return 0
    }
    $count = 0
    foreach ($name in $ExpectedNames) {
        $manifestPath = Join-Path (Join-Path $RootPath $name) "manifest.json"
        if (Test-Path -LiteralPath $manifestPath) {
            $count += 1
        }
    }
    return $count
}

function Stop-ProcessTree {
    param([int]$ProcessId)
    $children = Get-CimInstance Win32_Process |
        Where-Object { $_.ParentProcessId -eq $ProcessId } |
        Select-Object -ExpandProperty ProcessId
    foreach ($childId in $children) {
        Stop-ProcessTree -ProcessId $childId
    }
    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
}

function Join-ArgumentList {
    param([string[]]$Arguments)
    return (($Arguments | ForEach-Object {
        if ($_ -match '[\s"]') {
            '"' + ($_ -replace '"', '\"') + '"'
        } else {
            $_
        }
    }) -join " ")
}

function Write-FinalSummary {
    param(
        [string]$InputRootPath,
        [string]$OutputRootPath,
        [string]$LogRootPath,
        [string]$Mode,
        [int]$SupportedCount,
        [int]$ExpectedCount,
        [int]$FinalManifestCount,
        [int]$CompletedExpectedCount,
        [int]$FailedManifestCount,
        [int]$AttemptCount,
        [int]$TimeoutRestartCount,
        [int]$MaxAttemptCount,
        [int]$TimeoutMinuteCount,
        [bool]$TargetReached,
        [string]$FinalStatus,
        [string]$PythonPath
    )
    Write-Host ""
    Write-Host "office2md runner final summary"
    Write-Host "Input: $InputRootPath"
    Write-Host "Output: $OutputRootPath"
    Write-Host "Logs: $LogRootPath"
    Write-Host "Mode: $Mode"
    Write-Host "Supported files: $SupportedCount"
    Write-Host "Expected unique manifests: $ExpectedCount"
    Write-Host "Final manifest count: $FinalManifestCount"
    Write-Host "Completed expected manifests: $CompletedExpectedCount/$ExpectedCount"
    Write-Host "Failed manifests: $FailedManifestCount"
    Write-Host "Attempts used: $AttemptCount"
    Write-Host "Timeout/restart count: $TimeoutRestartCount"
    Write-Host "Max attempts: $MaxAttemptCount"
    Write-Host "Timeout minutes per attempt: $TimeoutMinuteCount"
    Write-Host "Target reached: $TargetReached"
    Write-Host "Final status: $FinalStatus"
    Write-Host "Log location: $LogRootPath"
    Write-Host "Next recommended command:"
    Write-Host "`"$PythonPath`" -m office2md.cli build-library `"$OutputRootPath`" `"<library_output_dir>`""
}

$pythonPath = Resolve-Office2MdPath $Python
$inputRoot = Resolve-Office2MdPath $InputPath
$outputRoot = Resolve-Office2MdPath $OutputPath
if (-not $LogDirectory) {
    $LogDirectory = Join-Path $outputRoot "_logs"
}
$logRoot = Resolve-Office2MdPath $LogDirectory

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "Python executable not found: $pythonPath"
}
if (-not (Test-Path -LiteralPath $inputRoot)) {
    throw "Input path not found: $inputRoot"
}
if ($MaxFiles -le 0 -and -not $FullDirectory) {
    throw "Set -MaxFiles or pass -FullDirectory."
}
if ($TimeoutMinutes -lt 1) {
    throw "TimeoutMinutes must be at least 1."
}
if ($MaxAttempts -lt 1) {
    throw "MaxAttempts must be at least 1."
}

$expectedCounts = Get-ExpectedManifestCount -PythonPath $pythonPath -RootPath $inputRoot -OutputRootPath $outputRoot -MaxFileCount $MaxFiles
$supportedCount = $expectedCounts.Supported
$expected = $expectedCounts.Expected
$expectedNames = $expectedCounts.Names
$mode = if ($FullDirectory) { "FullDirectory" } else { "MaxFiles $MaxFiles" }
$timeoutRestartCount = 0
$attemptsUsed = 0

$baseArgs = @(
    "-m", "office2md.cli", "convert",
    $inputRoot,
    $outputRoot,
    "--recursive",
    "--engine", "auto",
    "--profile", "kb",
    "--render-pdf-pages",
    "--max-render-pages", "3",
    "--max-text-pages", "10",
    "--no-force-ocr",
    "--no-use-ai",
    "--ai-backend", "none",
    "--skip-existing"
)
if ($MaxFiles -gt 0) {
    $baseArgs += @("--max-files", [string]$MaxFiles)
}
$argumentText = Join-ArgumentList -Arguments $baseArgs

Write-Host "office2md chunked/resume convert runner"
Write-Host "Input: $inputRoot"
Write-Host "Output: $outputRoot"
Write-Host "Logs: $logRoot"
Write-Host "Supported files: $supportedCount"
Write-Host "Expected unique manifests: $expected"
Write-Host "Timeout minutes per attempt: $TimeoutMinutes"
Write-Host "Max attempts: $MaxAttempts"
Write-Host "Command: `"$pythonPath`" $argumentText"

if ($DryRun) {
    Write-Host "Dry run only. No conversion started."
    Write-FinalSummary `
        -InputRootPath $inputRoot `
        -OutputRootPath $outputRoot `
        -LogRootPath $logRoot `
        -Mode "$mode (DryRun)" `
        -SupportedCount $supportedCount `
        -ExpectedCount $expected `
        -FinalManifestCount (Get-ManifestCount -RootPath $outputRoot) `
        -CompletedExpectedCount (Get-ExpectedManifestPresentCount -RootPath $outputRoot -ExpectedNames $expectedNames) `
        -FailedManifestCount (Get-FailedManifestCount -RootPath $outputRoot) `
        -AttemptCount 0 `
        -TimeoutRestartCount 0 `
        -MaxAttemptCount $MaxAttempts `
        -TimeoutMinuteCount $TimeoutMinutes `
        -TargetReached $false `
        -FinalStatus "dry-run" `
        -PythonPath $pythonPath
    exit 0
}

New-Item -ItemType Directory -Path $outputRoot -Force | Out-Null
New-Item -ItemType Directory -Path $logRoot -Force | Out-Null

for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
    $attemptsUsed = $attempt
    $manifestCount = Get-ExpectedManifestPresentCount -RootPath $outputRoot -ExpectedNames $expectedNames
    $totalManifestCount = Get-ManifestCount -RootPath $outputRoot
    if ($manifestCount -ge $expected) {
        $failedManifestCount = Get-FailedManifestCount -RootPath $outputRoot
        $finalStatus = if ($failedManifestCount -gt 0) { "needs review" } else { "success" }
        Write-Host "Done: $manifestCount/$expected expected manifests present ($totalManifestCount total manifests)."
        Write-FinalSummary `
            -InputRootPath $inputRoot `
            -OutputRootPath $outputRoot `
            -LogRootPath $logRoot `
            -Mode $mode `
            -SupportedCount $supportedCount `
            -ExpectedCount $expected `
            -FinalManifestCount $totalManifestCount `
            -CompletedExpectedCount $manifestCount `
            -FailedManifestCount $failedManifestCount `
            -AttemptCount ($attempt - 1) `
            -TimeoutRestartCount $timeoutRestartCount `
            -MaxAttemptCount $MaxAttempts `
            -TimeoutMinuteCount $TimeoutMinutes `
            -TargetReached $true `
            -FinalStatus $finalStatus `
            -PythonPath $pythonPath
        exit 0
    }

    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $stdoutLog = Join-Path $logRoot ("convert_attempt_{0:D2}_{1}.out.log" -f $attempt, $stamp)
    $stderrLog = Join-Path $logRoot ("convert_attempt_{0:D2}_{1}.err.log" -f $attempt, $stamp)

    Write-Host "Attempt $attempt starting at $(Get-Date -Format o); expected manifests before: $manifestCount/$expected ($totalManifestCount total)"
    $process = Start-Process -FilePath $pythonPath `
        -ArgumentList $argumentText `
        -WorkingDirectory (Get-Location) `
        -NoNewWindow `
        -PassThru `
        -RedirectStandardOutput $stdoutLog `
        -RedirectStandardError $stderrLog

    $finished = Wait-Process -Id $process.Id -Timeout ($TimeoutMinutes * 60) -ErrorAction SilentlyContinue
    if ($null -eq $finished) {
        Write-Warning "Attempt $attempt exceeded $TimeoutMinutes minutes. Stopping process tree for PID $($process.Id)."
        $timeoutRestartCount += 1
        Stop-ProcessTree -ProcessId $process.Id
    } else {
        Write-Host "Attempt $attempt exited with code $($process.ExitCode)."
        if ($process.ExitCode -ne 0) {
            Write-Warning "Non-zero exit code. Continuing while progress is possible; inspect $stderrLog."
        }
    }

    Start-Sleep -Seconds 2
    $afterCount = Get-ExpectedManifestPresentCount -RootPath $outputRoot -ExpectedNames $expectedNames
    $afterTotalCount = Get-ManifestCount -RootPath $outputRoot
    Write-Host "Attempt $attempt complete; expected manifests after: $afterCount/$expected ($afterTotalCount total)"
}

$finalCount = Get-ExpectedManifestPresentCount -RootPath $outputRoot -ExpectedNames $expectedNames
$finalTotalCount = Get-ManifestCount -RootPath $outputRoot
$finalFailedManifestCount = Get-FailedManifestCount -RootPath $outputRoot
$targetReached = $finalCount -ge $expected
$finalStatus = if ($targetReached) { "needs review" } else { "incomplete" }
Write-FinalSummary `
    -InputRootPath $inputRoot `
    -OutputRootPath $outputRoot `
    -LogRootPath $logRoot `
    -Mode $mode `
    -SupportedCount $supportedCount `
    -ExpectedCount $expected `
    -FinalManifestCount $finalTotalCount `
    -CompletedExpectedCount $finalCount `
    -FailedManifestCount $finalFailedManifestCount `
    -AttemptCount $attemptsUsed `
    -TimeoutRestartCount $timeoutRestartCount `
    -MaxAttemptCount $MaxAttempts `
    -TimeoutMinuteCount $TimeoutMinutes `
    -TargetReached $targetReached `
    -FinalStatus $finalStatus `
    -PythonPath $pythonPath
throw "Reached MaxAttempts=$MaxAttempts with $finalCount/$expected expected manifests ($finalTotalCount total manifests)."
