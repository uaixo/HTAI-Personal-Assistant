# NousAI Phase 1 installer (Windows).
# Copies the skin and persona into the Hermes home directory — never touches the repo.
$ErrorActionPreference = "Stop"

$Src = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($env:HERMES_HOME) {
    $HermesDir = $env:HERMES_HOME
} else {
    $HermesDir = Join-Path $env:LOCALAPPDATA "hermes"
}

Write-Host "Installing NousAI Phase 1 into: $HermesDir"
New-Item -ItemType Directory -Force -Path (Join-Path $HermesDir "skins") | Out-Null

Copy-Item (Join-Path $Src "skins\nousai.yaml") (Join-Path $HermesDir "skins\nousai.yaml") -Force
Write-Host "  OK skin  -> $HermesDir\skins\nousai.yaml"

$Soul = Join-Path $HermesDir "SOUL.md"
if (Test-Path $Soul) {
    $Backup = "$Soul.bak-$(Get-Date -Format yyyyMMddHHmmss)"
    Copy-Item $Soul $Backup
    Write-Host "  existing SOUL.md backed up -> $Backup"
}
Copy-Item (Join-Path $Src "SOUL.md") $Soul -Force
Write-Host "  OK persona -> $Soul"

$Config = Join-Path $HermesDir "config.yaml"
if (-not (Test-Path $Config)) {
    "display:`n  skin: nousai`ndashboard:`n  theme: nousai`n" | Set-Content -Encoding UTF8 $Config
    Write-Host "  OK config  -> $Config (display.skin + dashboard.theme: nousai)"
} else {
    Write-Host "  config.yaml already exists - left untouched."
    Write-Host "    Activate the skin by running '/skin nousai' inside Hermes (persists automatically),"
    Write-Host "    or set 'display.skin: nousai' and 'dashboard.theme: nousai' in $Config yourself."
}

Write-Host "Done. Start hermes and the banner should greet you as NousAI."
