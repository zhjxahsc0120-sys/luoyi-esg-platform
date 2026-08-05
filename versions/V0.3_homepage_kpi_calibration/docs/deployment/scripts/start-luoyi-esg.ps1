$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$BackendUrl = "http://127.0.0.1:8765"
$FrontendUrl = "http://localhost:5173/#/"
$GisPreviewUrl = "http://localhost:5173/#/gis-preview"
$WorkspaceUrl = "http://localhost:5173/#/workspace"
$GaodeTileUrl = "https://webst01.is.autonavi.com/appmaptile?style=6&x=205&y=110&z=8"
$MySqlPort = 3307
$MySqlExe = "E:\Mysql\mysql-8.4.9-winx64\bin\mysqld.exe"
$MySqlCnf = "E:\Mysql\my-luoyi.cnf"
$MySqlLog = "E:\Mysql\logs\luoyi-mysql.err"

function Write-Step($Text) {
  Write-Host ""
  Write-Host "==> $Text" -ForegroundColor Cyan
}

function Test-TcpPort($HostName, $Port) {
  try {
    $Client = [System.Net.Sockets.TcpClient]::new()
    $Async = $Client.BeginConnect($HostName, $Port, $null, $null)
    $Ok = $Async.AsyncWaitHandle.WaitOne(800)
    if (-not $Ok) {
      $Client.Close()
      return $false
    }
    $Client.EndConnect($Async)
    $Client.Close()
    return $true
  } catch {
    return $false
  }
}

function Test-HttpOk($Url, $TimeoutSec = 3) {
  try {
    $Response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec
    return [int]$Response.StatusCode -ge 200 -and [int]$Response.StatusCode -lt 400
  } catch {
    return $false
  }
}

function Test-JsonApiCodeOk($Url, $TimeoutSec = 3) {
  try {
    $Response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec
    if ([int]$Response.StatusCode -lt 200 -or [int]$Response.StatusCode -ge 400) {
      return $false
    }
    $Body = $Response.Content | ConvertFrom-Json
    if ($null -ne $Body.code) {
      return [int]$Body.code -eq 0
    }
    return $true
  } catch {
    return $false
  }
}

function Start-LuoyiMySql() {
  if (Test-TcpPort "127.0.0.1" $MySqlPort) {
    Write-Host "MySQL port $MySqlPort is reachable." -ForegroundColor Green
    return $true
  }

  Write-Host "MySQL port $MySqlPort is not reachable. Trying to start local MySQL..." -ForegroundColor Yellow

  if (-not (Test-Path $MySqlExe)) {
    Write-Host "MySQL executable not found: $MySqlExe" -ForegroundColor Red
    return $false
  }

  if (-not (Test-Path $MySqlCnf)) {
    Write-Host "MySQL config not found: $MySqlCnf" -ForegroundColor Red
    return $false
  }

  Start-Process `
    -FilePath $MySqlExe `
    -ArgumentList "--defaults-file=$MySqlCnf" `
    -WorkingDirectory (Split-Path -Parent $MySqlExe) `
    -WindowStyle Hidden

  for ($i = 0; $i -lt 25; $i++) {
    if (Test-TcpPort "127.0.0.1" $MySqlPort) {
      Write-Host "MySQL started on port $MySqlPort." -ForegroundColor Green
      return $true
    }
    Start-Sleep -Seconds 1
  }

  Write-Host "MySQL did not become ready within 25 seconds." -ForegroundColor Red
  if (Test-Path $MySqlLog) {
    Write-Host "Last MySQL log lines:" -ForegroundColor Yellow
    Get-Content $MySqlLog -Tail 12
  }
  return $false
}

Set-Location $Root

Write-Host "Project root: $Root"

Write-Step "Start or check MySQL 127.0.0.1:$MySqlPort"
if (Start-LuoyiMySql) {
  Write-Host "MySQL is ready for project data." -ForegroundColor Green
} else {
  throw "MySQL startup failed; backend startup stopped."
}

Write-Step "Apply E01 V1.1 migrations and professional seed data"
python -m server.migrations.e_group_e01_v1_1.migrate_v1_1
if ($LASTEXITCODE -ne 0) {
  throw "E01 V1.1 migration failed."
}

Write-Step "Start backend API"
if (Test-HttpOk "$BackendUrl/health") {
  Write-Host "Backend API is already running: $BackendUrl" -ForegroundColor Green
} else {
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root "server\start_backend.ps1")
  Start-Sleep -Seconds 2
}

if (Test-HttpOk "$BackendUrl/health") {
  Write-Host "Backend API is ready: $BackendUrl" -ForegroundColor Green
  $HealthBody = (Invoke-WebRequest -Uri "$BackendUrl/health" -UseBasicParsing -TimeoutSec 5).Content | ConvertFrom-Json
  if (-not $HealthBody.mysql.ok) {
    throw "Backend is running but its MySQL connection is not ready."
  }
} else {
  Write-Host "Backend API health check failed." -ForegroundColor Red
  Write-Host "Check logs: server\server.log and server\server.err.log" -ForegroundColor Red
  throw "Backend API health check failed."
}

Write-Step "Check GIS API"
if (Test-JsonApiCodeOk "$BackendUrl/api/esg/gis/layers?projectId=LUOYI-ESG") {
  Write-Host "GIS layers API is OK: $BackendUrl/api/esg/gis/layers" -ForegroundColor Green
} else {
  Write-Host "GIS layers API is not ready. Check backend and database." -ForegroundColor Yellow
}

Write-Step "Check online satellite tile"
if (Test-HttpOk $GaodeTileUrl 8) {
  Write-Host "Gaode satellite tile is reachable." -ForegroundColor Green
} else {
  Write-Host "Gaode satellite tile is not reachable. GIS may show only base color and business layers." -ForegroundColor Yellow
}

Write-Step "Start frontend Vite on port 5173"
if (Test-TcpPort "127.0.0.1" 5173) {
  Write-Host "Frontend port 5173 is already running: $FrontendUrl" -ForegroundColor Green
} else {
  $Command = "Set-Location '$Root'; npm.cmd run dev -- --host 127.0.0.1 --port 5173"
  Start-Process `
    -FilePath "powershell.exe" `
    -ArgumentList "-NoExit", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $Command `
    -WorkingDirectory $Root `
    -WindowStyle Minimized
  Write-Host "Frontend Vite window started. Waiting for port 5173..." -ForegroundColor Green

  for ($i = 0; $i -lt 20; $i++) {
    if (Test-TcpPort "127.0.0.1" 5173) { break }
    Start-Sleep -Seconds 1
  }
}

if (-not (Test-TcpPort "127.0.0.1" 5173)) {
  throw "Frontend Vite did not become ready on port 5173."
}

Write-Step "Open browser"
Start-Process $FrontendUrl

Write-Host ""
Write-Host "Startup complete." -ForegroundColor Green
Write-Host "Dashboard: $FrontendUrl"
Write-Host "GIS preview: $GisPreviewUrl"
Write-Host "Workspace: $WorkspaceUrl"
Write-Host ""
Write-Host "If GIS is not visible, press Ctrl+F5 in the browser." -ForegroundColor Yellow
