# Lance la surveillance continue
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Création de l'environnement virtuel..."
    python -m venv .venv
    .\.venv\Scripts\pip install -r requirements.txt -q
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Fichier .env créé — configurez Telegram avant de recevoir des alertes."
}

.\.venv\Scripts\python monitor.py
