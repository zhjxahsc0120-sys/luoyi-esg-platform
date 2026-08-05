$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$FrontendDir = Join-Path $Root 'frontend'
$LogFile = Join-Path $FrontendDir 'vite.log'
$ErrFile = Join-Path $FrontendDir 'vite.err.log'

if (Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue) {
  Write-Host 'Vite already listens on 5173.' -ForegroundColor Green
  exit 0
}

Start-Process -FilePath 'npm.cmd' `
  -ArgumentList @('run','dev','--','--host','127.0.0.1','--port','5173') `
  -WorkingDirectory $FrontendDir `
  -RedirectStandardOutput $LogFile `
  -RedirectStandardError $ErrFile `
  -WindowStyle Hidden | Out-Null
Start-Sleep -Seconds 2

if (-not (Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue)) {
  throw 'Vite did not become ready on port 5173.'
}
Write-Host 'Vite ready: http://localhost:5173/#/' -ForegroundColor Green
