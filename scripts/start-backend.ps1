$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$BackendDir = Join-Path $Root 'backend'
$PidFile = Join-Path $BackendDir 'server.pid'
$LogFile = Join-Path $BackendDir 'server.log'
$ErrFile = Join-Path $BackendDir 'server.err.log'

if (Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue) {
  Write-Host 'Python API already listens on 8765.' -ForegroundColor Green
  exit 0
}

$Python = (Get-Command python -CommandType Application -ErrorAction Stop).Source
$Process = Start-Process -FilePath $Python `
  -ArgumentList 'app.py' `
  -WorkingDirectory $BackendDir `
  -RedirectStandardOutput $LogFile `
  -RedirectStandardError $ErrFile `
  -WindowStyle Hidden `
  -PassThru
$Process.Id | Set-Content -Path $PidFile -Encoding ASCII
Start-Sleep -Seconds 1

$health = Invoke-WebRequest -Uri 'http://127.0.0.1:8765/health' -UseBasicParsing -TimeoutSec 5
Write-Host $health.Content
