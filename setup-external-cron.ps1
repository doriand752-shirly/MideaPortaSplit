# Declencheur externe fiable si le cron GitHub ne tourne pas (repos recents).
# Prerequis : gh auth login

$Owner = "doriand752-shirly"
$Repo = "MideaPortaSplit"
$Workflow = "monitor.yml"

Write-Host ""
Write-Host "=== Cron externe pour PortaSplit Monitor ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Le cron GitHub (schedule) peut rester muet 24h+ sur un repo neuf."
Write-Host "Solution : cron-job.org (gratuit) appelle le workflow toutes les 10 min."
Write-Host ""
Write-Host "1. Creer un token GitHub (Fine-grained) :" -ForegroundColor Yellow
Write-Host "   https://github.com/settings/tokens?type=beta"
Write-Host "   - Repository access : $Owner/$Repo"
Write-Host "   - Permissions : Actions = Read and write"
Write-Host ""
Write-Host "2. Sur https://cron-job.org/en/ creer un job :" -ForegroundColor Yellow
Write-Host "   - URL : https://api.github.com/repos/$Owner/$Repo/dispatches"
Write-Host "   - Method : POST"
Write-Host "   - Schedule : */10 * * * *"
Write-Host "   - Headers :"
Write-Host "       Accept: application/vnd.github+json"
Write-Host "       Authorization: Bearer VOTRE_TOKEN"
Write-Host "       X-GitHub-Api-Version: 2022-11-28"
Write-Host "   - Body (JSON) : { `"event_type`": `"monitor`" }"
Write-Host ""
Write-Host "3. Tester maintenant avec gh (sans token externe) :" -ForegroundColor Yellow
Write-Host ""

$run = Read-Host "Lancer un run manuel maintenant ? (o/N)"
if ($run -eq "o" -or $run -eq "O") {
    gh workflow run "PortaSplit Monitor"
    Start-Sleep -Seconds 5
    gh run list --workflow="PortaSplit Monitor" --limit 1
}

Write-Host ""
Write-Host "Historique : https://github.com/$Owner/$Repo/actions" -ForegroundColor Green
