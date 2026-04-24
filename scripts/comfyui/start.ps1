param(
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 8188,
    [switch]$AllowLan
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$venvPython = Join-Path $root ".venv-comfyui\Scripts\python.exe"
$comfyRoot = Join-Path $root "comfyui\ComfyUI"
$tmpRoot = Join-Path $root "tmp\comfyui"
$pidFile = Join-Path $tmpRoot "comfyui.pid"
$metaFile = Join-Path $tmpRoot "comfyui-session.json"
$stdoutLog = Join-Path $tmpRoot "comfyui.stdout.log"
$stderrLog = Join-Path $tmpRoot "comfyui.stderr.log"
$whisperCudaDir = Join-Path $root "local_whisper\vendor\cuda12"

New-Item -ItemType Directory -Force -Path $tmpRoot | Out-Null

if (-not (Test-Path $venvPython)) {
    throw "Missing Python runtime: $venvPython"
}

if (-not (Test-Path $comfyRoot)) {
    throw "Missing ComfyUI checkout: $comfyRoot"
}

if (Test-Path $pidFile) {
    $existingPid = (Get-Content $pidFile -Raw).Trim()
    if ($existingPid) {
        $existingProc = Get-Process -Id ([int]$existingPid) -ErrorAction SilentlyContinue
        if ($existingProc) {
            Write-Output "ComfyUI is already running with PID $existingPid on http://$BindHost`:$Port"
            exit 0
        }
    }
}

$listenHost = if ($AllowLan) { "0.0.0.0" } else { $BindHost }
$arguments = @("main.py", "--listen", $listenHost, "--port", "$Port", "--dont-print-server")

$originalPath = $env:PATH
$originalDisableProgress = $env:COMFYUI_DISABLE_PROGRESS_BAR
if (Test-Path $whisperCudaDir) {
    $env:PATH = "$whisperCudaDir;$env:PATH"
}
$env:COMFYUI_DISABLE_PROGRESS_BAR = "1"

try {
    $process = Start-Process `
        -FilePath $venvPython `
        -ArgumentList $arguments `
        -WorkingDirectory $comfyRoot `
        -RedirectStandardOutput $stdoutLog `
        -RedirectStandardError $stderrLog `
        -PassThru
} finally {
    $env:PATH = $originalPath
    if ($null -eq $originalDisableProgress) {
        Remove-Item Env:COMFYUI_DISABLE_PROGRESS_BAR -ErrorAction SilentlyContinue
    } else {
        $env:COMFYUI_DISABLE_PROGRESS_BAR = $originalDisableProgress
    }
}

$process.Id | Set-Content -Path $pidFile -Encoding ascii

$session = [ordered]@{
    pid = $process.Id
    host = $listenHost
    port = $Port
    started_at = (Get-Date).ToString("o")
    stdout_log = $stdoutLog
    stderr_log = $stderrLog
}
$session | ConvertTo-Json | Set-Content -Path $metaFile -Encoding utf8

$deadline = (Get-Date).AddSeconds(90)
$ready = $false
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 2
    try {
        $probe = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port/system_stats" -TimeoutSec 5
        $ready = $true
        break
    } catch {
    }
    if (-not (Get-Process -Id $process.Id -ErrorAction SilentlyContinue)) {
        break
    }
}

if (-not (Get-Process -Id $process.Id -ErrorAction SilentlyContinue)) {
    throw "ComfyUI failed to become ready. Check logs:`n$stdoutLog`n$stderrLog"
}

Write-Output "ComfyUI started."
Write-Output "URL: http://127.0.0.1:$Port"
Write-Output "PID: $($process.Id)"
Write-Output "Logs: $stdoutLog"
if (-not $ready) {
    Write-Output "API warmup is still in progress. Run .\\scripts\\comfyui\\status.ps1 in a few seconds."
}
