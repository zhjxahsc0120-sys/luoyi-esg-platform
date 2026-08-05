$ErrorActionPreference = 'SilentlyContinue'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$PidFile = Join-Path $Root 'backend\server.pid'
if (Test-Path $PidFile) {
  $PidValue = Get-Content $PidFile | Select-Object -First 1
  if ($PidValue) { Stop-Process -Id ([int]$PidValue) -Force }
  Remove-Item $PidFile -Force
}
