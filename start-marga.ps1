param(
  [switch]$Open
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$State = Join-Path $Root ".marga\state"
$LogOut = Join-Path $State "marga.stdout.log"
$LogErr = Join-Path $State "marga.stderr.log"
$PidFile = Join-Path $State "marga.pid"
$Port = if ($env:MARGA_PORT) { [int]$env:MARGA_PORT } else { 28779 }
$Url = "http://127.0.0.1:$Port"

if (-not (Test-Path $Python)) {
  throw "MARGA Python environment not found: $Python"
}

New-Item -ItemType Directory -Force -Path $State | Out-Null

# MARGA owns one stable local state root. Keep the legacy variable synchronized because
# inherited modules still read it. An explicit plugin gate remains authoritative.
$env:MARGA_STATE_DIR = $State
$env:JAVIS_STATE_DIR = $State
$newGate = [Environment]::GetEnvironmentVariable("JAVIS_ENABLE_USER_PLUGINS", "Process")
$oldGate = [Environment]::GetEnvironmentVariable("JAVIS_ENABLE_VAULT_PLUGINS", "Process")
if ([string]::IsNullOrWhiteSpace($newGate) -and [string]::IsNullOrWhiteSpace($oldGate)) {
  $env:JAVIS_ENABLE_USER_PLUGINS = "true"
}
$env:PYTHONPATH = Join-Path $Root "server"

try {
  $health = Invoke-WebRequest -UseBasicParsing "$Url/health" -TimeoutSec 2
  if ($health.StatusCode -eq 200) {
    Write-Host "MARGA is already running at $Url"
    if ($Open) { Start-Process $Url }
    exit 0
  }
} catch { }

$arguments = "-m uvicorn main:app --app-dir server --host 127.0.0.1 --port $Port"
$proc = Start-Process -FilePath $Python -ArgumentList $arguments -WorkingDirectory $Root `
  -WindowStyle Hidden -RedirectStandardOutput $LogOut -RedirectStandardError $LogErr -PassThru
$proc.Id | Set-Content -LiteralPath $PidFile -Encoding ascii

for ($i = 0; $i -lt 60; $i++) {
  Start-Sleep -Seconds 1
  try {
    $health = Invoke-WebRequest -UseBasicParsing "$Url/health" -TimeoutSec 2
    if ($health.StatusCode -eq 200) {
      Write-Host "MARGA started at $Url"
      Write-Host "Persistent state: $State"
      if ($Open) { Start-Process $Url }
      exit 0
    }
  } catch { }
}

throw "MARGA did not become healthy within 60 seconds. See $LogOut and $LogErr"
