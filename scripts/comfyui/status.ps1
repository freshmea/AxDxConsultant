param(
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 8188
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$tmpRoot = Join-Path $root "tmp\comfyui"
$pidFile = Join-Path $tmpRoot "comfyui.pid"
$metaFile = Join-Path $tmpRoot "comfyui-session.json"

$processId = $null
$processAlive = $false
if (Test-Path $pidFile) {
    $pidText = (Get-Content $pidFile -Raw).Trim()
    if ($pidText) {
        $processId = [int]$pidText
        $processAlive = [bool](Get-Process -Id $processId -ErrorAction SilentlyContinue)
    }
}

$apiReachable = $false
$gpuName = $null
try {
    $stats = Invoke-RestMethod -Uri "http://${BindHost}:$Port/system_stats" -TimeoutSec 5
    $apiReachable = $true
    if ($stats.devices -and $stats.devices.Count -gt 0) {
        $gpuName = $stats.devices[0].name
    }
} catch {
}

$result = [ordered]@{
    pid = $processId
    process_alive = $processAlive
    api_reachable = $apiReachable
    host = $BindHost
    port = $Port
    gpu = $gpuName
    session_file = $(if (Test-Path $metaFile) { $metaFile } else { $null })
}

$result | ConvertTo-Json
