param()

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$tmpRoot = Join-Path $root "tmp\comfyui"
$pidFile = Join-Path $tmpRoot "comfyui.pid"
$metaFile = Join-Path $tmpRoot "comfyui-session.json"

if (-not (Test-Path $pidFile)) {
    Write-Output "ComfyUI pid file not found."
    exit 0
}

$pidText = (Get-Content $pidFile -Raw).Trim()
if (-not $pidText) {
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    Write-Output "ComfyUI pid file was empty."
    exit 0
}

$processId = [int]$pidText
$process = Get-Process -Id $processId -ErrorAction SilentlyContinue
if ($process) {
    Stop-Process -Id $processId -Force
    Write-Output "Stopped ComfyUI process $processId."
} else {
    Write-Output "Process $processId is not running."
}

Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
Remove-Item $metaFile -Force -ErrorAction SilentlyContinue
