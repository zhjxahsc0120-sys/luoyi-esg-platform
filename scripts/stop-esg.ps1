$ErrorActionPreference = 'SilentlyContinue'

$Root = Split-Path -Parent $PSScriptRoot
$RuntimeDir = Join-Path $Root 'runtime'

function Stop-PidFile([string]$Name, [string]$Label) {
  $pidFile = Join-Path $RuntimeDir $Name
  if (-not (Test-Path -LiteralPath $pidFile)) { return }
  $pidValue = Get-Content -LiteralPath $pidFile | Select-Object -First 1
  if ($pidValue -and ($pidValue -as [int])) {
    $process = Get-Process -Id ([int]$pidValue) -ErrorAction SilentlyContinue
    if ($process) {
      Stop-Process -Id $process.Id -Force
      Write-Host "$Label stopped: $($process.Id)"
    }
  }
  Remove-Item -LiteralPath $pidFile -Force
}

Stop-PidFile 'frontend.pid' '前端'
Stop-PidFile 'backend.pid' '后端'

$mysqlProcesses = Get-CimInstance Win32_Process | Where-Object {
  $_.Name -eq 'mysqld.exe' -and $_.CommandLine -like '*my-luoyi.cnf*'
}
foreach ($process in $mysqlProcesses) {
  Stop-Process -Id $process.ProcessId -Force
  Write-Host "MySQL stopped: $($process.ProcessId)"
}
Remove-Item -LiteralPath (Join-Path $RuntimeDir 'mysql.pid') -Force

Write-Host 'ESG project stopped' -ForegroundColor Yellow
