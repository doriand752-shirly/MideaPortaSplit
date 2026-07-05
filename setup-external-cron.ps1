# Declencheur cron-job.org pour PortaSplit Monitor (seule source de planification).
# Prerequis : gh auth login

$Owner = "doriand752-shirly"
$Repo = "MideaPortaSplit"

Write-Host ""
Write-Host "=== Cron externe PortaSplit Monitor ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Le workflow GitHub n'a PAS de cron natif (schedule)."
Write-Host "La planification passe uniquement par cron-job.org (toutes les 10 min)."
Write-Host ""
Write-Host "Job existant : https://console.cron-job.org (PortaSplit Monitor)" -ForegroundColor Green
Write-Host ""
Write-Host "Pour recreer le job manuellement :" -ForegroundColor Yellow
Write-Host "   - URL : https://api.github.com/repos/$Owner/$Repo/dispatches"
Write-Host "   - Method : POST"
Write-Host "   - Schedule : */10 * * * * (Europe/Paris)"
Write-Host "   - Headers :"
Write-Host "       Accept: application/vnd.github+json"
Write-Host "       Authorization: Bearer VOTRE_TOKEN_GITHUB"
Write-Host "       X-GitHub-Api-Version: 2022-11-28"
Write-Host "   - Body (JSON) : { `"event_type`": `"monitor`" }"
Write-Host ""
Write-Host "Token GitHub : https://github.com/settings/tokens?type=beta"
Write-Host "   Repository $Owner/$Repo, permission Actions = Read and write"
Write-Host ""

$run = Read-Host "Lancer un run manuel maintenant ? (o/N)"
if ($run -eq "o" -or $run -eq "O") {
    gh workflow run "PortaSplit Monitor"
    Start-Sleep -Seconds 5
    gh run list --workflow="PortaSplit Monitor" --limit 1
}

Write-Host ""
Write-Host "Historique : https://github.com/$Owner/$Repo/actions" -ForegroundColor Green
