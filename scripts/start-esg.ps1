$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $Root 'backend'
$FrontendDir = Join-Path $Root 'frontend'
$RuntimeDir = Join-Path $Root 'runtime'
$EnvFile = Join-Path $Root '.env'
$LegacyEnvFile = Join-Path $env:APPDATA 'TRAE SOLO CN\ModularData\ai-agent\work-mode-projects\6a53a1b3d0f497e311ecc95f\.env'
$Python = (Get-Command python.exe -CommandType Application -ErrorAction Stop).Source
$Npm = (Get-Command npm.cmd -CommandType Application -ErrorAction Stop).Source
$MysqlExe = 'E:\Mysql\mysql-8.4.9-winx64\bin\mysqld.exe'
$MysqlConfig = 'E:\Mysql\my-luoyi.cnf'

New-Item -ItemType Directory -Path $RuntimeDir -Force | Out-Null

function Import-ProjectEnv {
  $envSources = @($EnvFile, $LegacyEnvFile)
  foreach ($source in $envSources) {
    if (Test-Path -LiteralPath $source) {
      foreach ($line in Get-Content -LiteralPath $source) {
        if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)=(.*)$') {
          Set-Item -Path ("Env:" + $matches[1]) -Value $matches[2].Trim().Trim('"').Trim("'")
        }
      }
      if ($env:LUOYI_MYSQL_PASSWORD) { break }
    }
  }
  if (-not $env:LUOYI_MYSQL_PASSWORD) {
    throw 'Database credentials unavailable. Configure C:\ESG_Project\.env or the existing local project environment before starting.'
  }
  $env:LUOYI_DB_MODE = 'mysql'
  if (-not $env:LUOYI_MYSQL_HOST) { $env:LUOYI_MYSQL_HOST = '127.0.0.1' }
  if (-not $env:LUOYI_MYSQL_PORT) { $env:LUOYI_MYSQL_PORT = '3307' }
  if (-not $env:LUOYI_MYSQL_DATABASE) { $env:LUOYI_MYSQL_DATABASE = 'luoyi_esg' }
  if (-not $env:LUOYI_MYSQL_USER) { $env:LUOYI_MYSQL_USER = 'luoyi_app' }
}

function Wait-Listening([int]$Port, [int]$Seconds = 30) {
  for ($i = 0; $i -lt $Seconds; $i++) {
    if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) { return }
    Start-Sleep -Seconds 1
  }
  throw "Port $Port did not listen within $Seconds seconds"
}

Import-ProjectEnv

if (-not (Get-NetTCPConnection -LocalPort 3307 -State Listen -ErrorAction SilentlyContinue)) {
  if (-not (Test-Path -LiteralPath $MysqlExe)) { throw "MySQL executable not found: $MysqlExe" }
  if (-not (Test-Path -LiteralPath $MysqlConfig)) { throw "MySQL config not found: $MysqlConfig" }
  $mysqlProcess = Start-Process -FilePath $MysqlExe -ArgumentList "--defaults-file=$MysqlConfig" -WorkingDirectory (Split-Path -Parent $MysqlExe) -WindowStyle Hidden -PassThru
  $mysqlProcess.Id | Set-Content -LiteralPath (Join-Path $RuntimeDir 'mysql.pid') -Encoding ASCII
  Wait-Listening 3307
}

if (-not (Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue)) {
  $backendProcess = Start-Process -FilePath $Python `
    -ArgumentList 'app.py' `
    -WorkingDirectory $BackendDir `
    -RedirectStandardOutput (Join-Path $RuntimeDir 'backend.log') `
    -RedirectStandardError (Join-Path $RuntimeDir 'backend.err.log') `
    -WindowStyle Hidden `
    -PassThru
  $backendProcess.Id | Set-Content -LiteralPath (Join-Path $RuntimeDir 'backend.pid') -Encoding ASCII
  Wait-Listening 8765
}

$health = Invoke-RestMethod -Uri 'http://127.0.0.1:8765/health' -TimeoutSec 10
if (-not $health.ok -or -not $health.mysql.ok) { throw 'Backend health check failed or MySQL is unavailable' }

if (-not (Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue)) {
  $frontendProcess = Start-Process -FilePath $Npm `
    -ArgumentList @('run','dev','--','--host','127.0.0.1','--port','5173') `
    -WorkingDirectory $FrontendDir `
    -RedirectStandardOutput (Join-Path $RuntimeDir 'frontend.log') `
    -RedirectStandardError (Join-Path $RuntimeDir 'frontend.err.log') `
    -WindowStyle Hidden `
    -PassThru
  $frontendProcess.Id | Set-Content -LiteralPath (Join-Path $RuntimeDir 'frontend.pid') -Encoding ASCII
  Wait-Listening 5173
}

Write-Host ''
Write-Host 'ESG project started' -ForegroundColor Green
Write-Host 'Frontend: http://localhost:5173/#/'
Write-Host 'Backend: http://127.0.0.1:8765/health'
Write-Host 'Database: 127.0.0.1:3307/luoyi_esg'
