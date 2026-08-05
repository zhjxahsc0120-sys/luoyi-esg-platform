$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$ServerDir = Join-Path $Root "server"
$RequirementsFile = Join-Path $ServerDir "requirements.txt"
$PidFile = Join-Path $ServerDir "server.pid"
$LogFile = Join-Path $ServerDir "server.log"
$ErrFile = Join-Path $ServerDir "server.err.log"

$PythonCommand = Get-Command python -CommandType Application -ErrorAction Stop
$Python = $PythonCommand.Source

Write-Host "Python runtime: $Python"

# Keep the backend on the same PATH Python used by the top-level launcher and
# bootstrap declared dependencies when this Python environment changes.
& $Python -c "import pymysql" 2>$null
if ($LASTEXITCODE -ne 0) {
  Write-Host "Installing backend Python dependencies..." -ForegroundColor Yellow
  & $Python -m pip install -r $RequirementsFile
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to install backend Python dependencies."
  }
}

if (Test-Path $PidFile) {
  $OldPid = (Get-Content $PidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
  if ($OldPid) {
    $Running = Get-Process -Id ([int]$OldPid) -ErrorAction SilentlyContinue
    if ($Running) {
      # BaseHTTP loads handlers at process start; recycle when server sources changed.
      $NewestSource = Get-ChildItem -Path $ServerDir -Filter "*.py" -File |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
      $NeedsReload = $NewestSource -and ($NewestSource.LastWriteTime -gt $Running.StartTime)
      if (-not $NeedsReload) {
        Write-Host "Luoyi ESG API already running. PID=$OldPid"
        Write-Host "Health: http://127.0.0.1:8765/health"
        exit 0
      }
      Write-Host "Backend sources changed since PID=$OldPid started; restarting..." -ForegroundColor Yellow
      Stop-Process -Id ([int]$OldPid) -Force -ErrorAction SilentlyContinue
      Start-Sleep -Seconds 1
      Remove-Item $PidFile -ErrorAction SilentlyContinue
    }
  }
}

& $Python (Join-Path $ServerDir "init_db.py")

$Proc = Start-Process `
  -FilePath $Python `
  -ArgumentList "server\app.py" `
  -WorkingDirectory $Root `
  -RedirectStandardOutput $LogFile `
  -RedirectStandardError $ErrFile `
  -PassThru `
  -WindowStyle Hidden

$Proc.Id | Set-Content -Path $PidFile -Encoding ASCII
Start-Sleep -Seconds 1

try {
  $Health = Invoke-WebRequest -Uri "http://127.0.0.1:8765/health" -UseBasicParsing -TimeoutSec 5
  Write-Host "Luoyi ESG API started. PID=$($Proc.Id)"
  Write-Host $Health.Content
} catch {
  Write-Host "Backend process started but health check failed. PID=$($Proc.Id)"
  Write-Host "Check logs:"
  Write-Host $LogFile
  Write-Host $ErrFile
  exit 1
}
