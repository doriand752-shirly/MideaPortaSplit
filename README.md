# Surveillance stock Midea PortaSplit

Outil Python qui surveille les principales pages de vente du **Midea PortaSplit** (MMCS-12HRN8-QRD0, 12 000 BTU, ~999 €) et vous alerte dès qu'un revendeur le remet en stock.

## Fonctionnalités

- Surveillance de 6 revendeurs actifs (Boulanger, Castorama, Optimea, Amazon + Darty/Leroy Merlin quand accessibles)
- Vérifications **parallèles** (6 en même temps) pour aller plus vite
- Parsers dédiés WooCommerce, Shopify, Amazon
- Alertes **Telegram**, **Discord** ou **ntfy.sh** (push mobile sans bot)
- Persistance de l'état pour ne pas renvoyer la même alerte
- Mode boucle (toutes les 5 min par défaut) ou vérification unique

## Installation

```powershell
cd c:\Users\doria\MideaPortaSplit
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

## Configuration Telegram

1. Ouvrez Telegram et parlez à **@BotFather** → `/newbot` → récupérez le **token**
2. Parlez à **@userinfobot** pour obtenir votre **chat_id**
3. Remplissez `.env` :

```env
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_CHAT_ID=987654321
CHECK_INTERVAL_MINUTES=5
```

4. Démarrez une conversation avec votre bot (bouton *Start*) avant la première alerte

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

## Limites

- Darty et Leroy Merlin bloquent parfois les requêtes automatiques (erreur 403). Surveillez-les aussi manuellement ou activez les alertes Dealabs.
- Les URLs ManoMano / Bricoman / Weldom peuvent changer ; mettez à jour `config.yaml` si une page renvoie une erreur.
- Méfiez-vous des prix > 1 200 € (revendeurs tiers) — le prix neuf attendu est **~999 €**.

## Structure

```
MideaPortaSplit/
├── monitor.py          # Point d'entrée
├── config.yaml         # Liste des revendeurs
├── .env                # Secrets (non versionné)
├── data/state.json     # Dernier état connu
└── src/
    ├── stock_checker.py
    ├── notifiers.py
    ├── state.py
    └── main.py
```
