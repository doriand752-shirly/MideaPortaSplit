# Surveillance stock Midea PortaSplit

Outil Python qui surveille les principales pages de vente du **Midea PortaSplit** (MMCS-12HRN8-QRD0, 12 000 BTU, ~999 €) et vous alerte dès qu'un revendeur le remet en stock.

## Fonctionnalités

- Surveillance de **9 revendeurs** (Boulanger, Castorama, Optimea, Darty, Leroy Merlin, Amazon, Fnac, ManoMano)
- Source **ClimRadar** pour le stock en ligne (Darty, Leroy Merlin, Amazon, Fnac, ManoMano)
- **Magasins locaux** : surveillance des points de vente dans un rayon configurable (ex. 100 km autour du 33400)
- Verification directe pour Boulanger, Castorama, Optimea
- Alertes **Telegram**, **Discord** ou **ntfy.sh** (push mobile sans bot)
- Persistance de l'état pour ne pas renvoyer la même alerte
- Mode boucle (toutes les 5 min par défaut) ou vérification unique

## Installation

```powershell
cd c:\Users\doria\MideaPortaSplit
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
copy .env.example .env
```

> **Darty / Leroy Merlin / Amazon** : surveilles via [ClimRadar](https://climradar.fr/produit/portasplit), un agrégateur qui met à jour le stock toutes les 10 minutes (y compris le stock par magasin pour Leroy Merlin).

Ou en une commande Windows :

```powershell
.\setup.ps1
```

## Configuration Telegram

1. Ouvrez Telegram et parlez à **@BotFather** → `/newbot` → récupérez le **token**
2. Parlez à **@userinfobot** pour obtenir votre **chat_id**
3. Remplissez `.env` :

```env
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_CHAT_ID=987654321
CHECK_INTERVAL_MINUTES=5
POSTAL_CODE=33400
LOCAL_RADIUS_KM=100
```

4. Démarrez une conversation avec votre bot (bouton *Start*) avant la première alerte

**Rapport quotidien à 18h** : un message « le moniteur tourne toujours » est envoyé chaque jour après 18h (configurable via `HEARTBEAT_HOUR` dans `.env`). Test : `python monitor.py --test-heartbeat`

### Critere d'alerte

Vous etes alerte uniquement si **l'une** de ces conditions est remplie :

1. **Magasin** : stock en retrait dans un magasin a moins de `LOCAL_RADIUS_KM` de `POSTAL_CODE` (ex. Castorama Merignac, Leroy Merlin Gradignan)
2. **Livraison** : stock en ligne avec livraison vers votre code postal (Boulanger, Castorama, Optimea, Darty, Amazon, Fnac, ManoMano)

Le stock Leroy Merlin « national » (ex. magasin a Nice) ne declenche pas d'alerte livraison vers Bordeaux — seulement un magasin proche de chez vous.

**Alternative sans Telegram — ntfy.sh :**

1. Installez l'app [ntfy](https://ntfy.sh) sur votre téléphone
2. Choisissez un topic secret (ex. `midea-doria-xyz123`)
3. Ajoutez dans `.env` : `NTFY_TOPIC=midea-doria-xyz123`
4. Abonnez-vous au même topic dans l'app

## Utilisation

**Démarrage rapide (Windows) :**

```powershell
.\start.ps1
```

**Une vérification (test) :**

```powershell
python monitor.py --once --dry-run
```

**Surveillance continue :**

```powershell
python monitor.py
```

**Vérification unique avec alertes :**

```powershell
python monitor.py --once
```

**Tester un seul revendeur :**

```powershell
python monitor.py --once --dry-run --retailer optimea
```

**Changer l'intervalle (ex. toutes les 2 minutes) :**

```powershell
python monitor.py --interval 2
```

## Personnaliser les revendeurs

Éditez `config.yaml` pour ajouter, retirer ou corriger des URLs. Chaque entrée :

```yaml
  - id: darty
    name: Darty
    url: https://www.darty.com/nav/achat/...
    expected_price: 999
```

## Lancer en arrière-plan (Windows)

**Planificateur de tâches** : créez une tâche qui exécute `python c:\Users\doria\MideaPortaSplit\monitor.py` au démarrage de session.

Ou en PowerShell :

```powershell
Start-Process python -ArgumentList "monitor.py" -WorkingDirectory "c:\Users\doria\MideaPortaSplit" -WindowStyle Hidden
```

## Surveillance 24/7 gratuite (GitHub Actions)

Le workflow `.github/workflows/monitor.yml` lance `python monitor.py --once --no-browser` **toutes les 5 minutes** (minimum GitHub) et envoie les alertes Telegram / ntfy / Discord.

### Secrets à configurer

Repo GitHub → **Settings** → **Secrets and variables** → **Actions** :

| Secret | Obligatoire | Exemple |
|--------|-------------|---------|
| `POSTAL_CODE` | oui | `33400` |
| `TELEGRAM_BOT_TOKEN` | un canal min. | token @BotFather |
| `TELEGRAM_CHAT_ID` | si Telegram | `987654321` |
| `NTFY_TOPIC` | si ntfy | `midea-doria-secret` |
| `LOCAL_RADIUS_KM` | non | `100` |
| `CONFIRM_STOCK` | non | `true` |

Poussez le repo sur GitHub, puis **Actions** → **PortaSplit Monitor** → **Run workflow** pour tester.

**Déjà configuré en local (`.env`) ?** Copiez les secrets en une commande :

```powershell
gh auth login
.\setup-github-secrets.ps1
```

L'état des alertes (`data/state.json`) est conservé via le cache Actions — pas de spam à chaque run.

## Limites

- ClimRadar peut indiquer du stock **régional** (ex. Leroy Merlin Nice) — vérifiez la livraison vers votre code postal.
- Le stock peut varier selon la region (ex. Darty : livraison Paris vs sud).
- Les URLs ManoMano / Bricoman / Weldom peuvent changer ; mettez `enabled: true` apres verification.
- Prix neuf attendu : **~999 EUR**. Ignorez les annonces > 1 200 EUR (revendeurs tiers).

## Structure

```
MideaPortaSplit/
├── monitor.py          # Point d'entrée
├── config.yaml         # Liste des revendeurs
├── .env                # Secrets (non versionné)
├── data/state.json     # Dernier état connu
└── src/
    ├── stock_checker.py
    ├── climradar.py
    ├── browser_fetcher.py
    ├── notifiers.py
    ├── state.py
    └── main.py
```

## App mobile (Expo)

Application iPhone/Android dans [`mobile/`](mobile/) — lancer avec `cd mobile && npx expo start`, puis scanner le QR code avec **Expo Go**.

Voir [`mobile/README.md`](mobile/README.md).

## App iOS native (optionnel)

Version SwiftUI dans [`ios/`](ios/) — nécessite un Mac avec Xcode.
