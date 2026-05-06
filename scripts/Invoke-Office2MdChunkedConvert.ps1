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

function Get-ScannerSupportedCount {
    param(
        [string]$PythonPath,
        [string]$RootPath
    )
    $code = "from pathlib import Path; import sys; from office2md.scanner import scan_input; print(len(scan_input(Path(sys.argv[1]), recursive=True)))"
    $output = & $PythonPath -c $code $RootPath
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to count supported files with office2md.scanner."
    }
    return [int]($output | Select-Object -Last 1)
}

function Get-ManifestCount {
    param([string]$RootPath)
    if (-not (Test-Path -LiteralPath $RootPath)) {
        return 0
    }
    return (Get-ChildItem -LiteralPath $RootPath -Recurse -Filter manifest.json -File -ErrorAction SilentlyContinue | Measure-Object).Count
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

$supportedCount = Get-ScannerSupportedCount -PythonPath $pythonPath -RootPath $inputRoot
$expected = $supportedCount
if ($MaxFiles -gt 0) {
    $expected = [Math]::Min($MaxFiles, $supportedCount)
}

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
Write-Host "Expected manifests: $expected"
Write-Host "Timeout minutes per attempt: $TimeoutMinutes"
Write-Host "Max attempts: $MaxAttempts"
Write-Host "Command: `"$pythonPath`" $argumentText"

if ($DryRun) {
    Write-Host "Dry run only. No conversion started."
    exit 0
}

New-Item -ItemType Directory -Path $outputRoot -Force | Out-Null
New-Item -ItemType Directory -Path $logRoot -Force | Out-Null

for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
    $manifestCount = Get-ManifestCount -RootPath $outputRoot
    if ($manifestCount -ge $expected) {
        Write-Host "Done: $manifestCount/$expected manifests present."
        exit 0
    }

    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $stdoutLog = Join-Path $logRoot ("convert_attempt_{0:D2}_{1}.out.log" -f $attempt, $stamp)
    $stderrLog = Join-Path $logRoot ("convert_attempt_{0:D2}_{1}.err.log" -f $attempt, $stamp)

    Write-Host "Attempt $attempt starting at $(Get-Date -Format o); manifests before: $manifestCount/$expected"
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
        Stop-ProcessTree -ProcessId $process.Id
    } else {
        Write-Host "Attempt $attempt exited with code $($process.ExitCode)."
        if ($process.ExitCode -ne 0) {
            Write-Warning "Non-zero exit code. Continuing while progress is possible; inspect $stderrLog."
        }
    }

    Start-Sleep -Seconds 2
    $afterCount = Get-ManifestCount -RootPath $outputRoot
    Write-Host "Attempt $attempt complete; manifests after: $afterCount/$expected"
}

$finalCount = Get-ManifestCount -RootPath $outputRoot
throw "Reached MaxAttempts=$MaxAttempts with $finalCount/$expected manifests."
