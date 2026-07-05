# Installation complete (une seule fois)
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    python -m venv .venv
}

.\.venv\Scripts\pip install -r requirements.txt -q
.\.venv\Scripts\playwright install chromium

Write-Host "Pret. Lancez .\start.ps1 pour demarrer la surveillance."
