# Copie les secrets du .env local vers GitHub Actions (une seule fois).
# Prérequis : gh auth login

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if (-not (Test-Path ".env")) {
    Write-Error "Fichier .env introuvable. Copiez .env.example en .env et remplissez-le."
    exit 1
}

$keys = @(
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "NTFY_TOPIC",
    "DISCORD_WEBHOOK_URL",
    "POSTAL_CODE",
    "LOCAL_RADIUS_KM",
    "CONFIRM_STOCK",
    "HEARTBEAT_ENABLED",
    "HEARTBEAT_HOUR"
)

$vars = @{}
Get-Content ".env" | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith("#")) { return }
    $eq = $line.IndexOf("=")
    if ($eq -lt 1) { return }
    $name = $line.Substring(0, $eq).Trim()
    $value = $line.Substring($eq + 1).Trim()
    if ($value.StartsWith('"') -and $value.EndsWith('"')) {
        $value = $value.Substring(1, $value.Length - 2)
    }
    $vars[$name] = $value
}

$set = 0
foreach ($key in $keys) {
    $value = $vars[$key]
    if (-not $value) { continue }
    Write-Host "Secret GitHub : $key"
    $value | gh secret set $key
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Echec pour $key — lancez 'gh auth login' puis réessayez."
        exit 1
    }
    $set++
}

if ($set -eq 0) {
    Write-Error "Aucun secret trouvé dans .env"
    exit 1
}

Write-Host ""
Write-Host "OK — $set secret(s) configuré(s) sur GitHub."
Write-Host "Poussez le repo si besoin, puis Actions -> PortaSplit Monitor -> Run workflow"
