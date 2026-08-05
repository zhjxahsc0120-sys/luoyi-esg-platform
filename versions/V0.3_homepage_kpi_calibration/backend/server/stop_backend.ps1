$ErrorActionPreference = "SilentlyContinue"

$ServerDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PidFile = Join-Path $ServerDir "server.pid"

if (-not (Test-Path $PidFile)) {
  Write-Host "No server.pid found. Backend may not be running."
  exit 0
}

$PidValue = Get-Content $PidFile | Select-Object -First 1
if (-not $PidValue) {
  Remove-Item $PidFile -Force
  Write-Host "Empty server.pid removed."
  exit 0
}

$Process = Get-Process -Id ([int]$PidValue)
if ($Process) {
  Stop-Process -Id ([int]$PidValue) -Force
  Write-Host "Luoyi ESG API stopped. PID=$PidValue"
} else {
  Write-Host "Backend process not found. PID=$PidValue"
}

Remove-Item $PidFile -Force
