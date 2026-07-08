# PortaSplit Monitor — app iOS

Application SwiftUI qui reprend la logique du moniteur Python (ClimRadar, magasins locaux, livraison).

## Limitation importante (iOS)

**Apple n’autorise pas une app à tourner en permanence en arrière-plan** comme un script sur PC.

| Mode | Fréquence | Fiabilité |
|------|-----------|-----------|
| App **ouverte** (écran allumé ou récent) | Toutes les 2 min (réglable) | ✅ Fiable |
| **Arrière-plan** (BGAppRefresh) | ~15–60 min, iOS décide | ⚠️ Best effort |
| **Moniteur PC + Telegram** | Toutes les 2 min | ✅ Recommandé pour 24/7 |

**Stratégie recommandée :** moniteur Python sur PC (ou cloud) + Telegram **+** cette app en complément quand vous avez le téléphone.

---

## Prérequis

- Mac avec **Xcode 15+**
- iPhone iOS **17+**
- Compte Apple Developer (gratuit suffit pour installer sur votre iPhone via câble)

---

## Installation (Mac)

### Option A — XcodeGen (rapide)

```bash
brew install xcodegen
cd ios
xcodegen generate
open PortaSplitMonitor.xcodeproj
```

1. Ouvrir le projet dans Xcode
2. **Signing & Capabilities** → choisir votre Team
3. Brancher l’iPhone → Run (▶)

### Option B — Création manuelle du projet

1. Xcode → **File → New → Project → iOS App**
2. Nom : `PortaSplitMonitor`, Interface **SwiftUI**, Language **Swift**
3. Supprimer les fichiers générés par défaut
4. Glisser-déposer le dossier `PortaSplitMonitor/` dans le projet
5. Remplacer `Info.plist` par celui du repo
6. **Signing & Capabilities** → ajouter **Background Modes** :
   - Background fetch
   - Background processing
7. Ajouter dans Info.plist (déjà présent dans le fichier fourni) :
   - `BGTaskSchedulerPermittedIdentifiers` → `fr.portasplit.monitor.refresh`

---

## Première utilisation

1. Autoriser les **notifications** au lancement
2. Onglet **Réglages** :
   - Code postal : `33000`
   - Rayon : `100 km`
   - Intervalle : `2 min`
3. Appuyer sur **Démarrer** (ou laisser l’app active au premier lancement)
4. **Test notification** pour vérifier les alertes

---

## Fonctionnalités

- ✅ Stock magasin (ClimRadar JSON, ex. LM Mérignac)
- ✅ Livraison en ligne (Darty, Boulanger, Amazon, etc.)
- ✅ Double vérification avant alerte (comme le Python)
- ✅ Notifications locales iOS
- ✅ Rafraîchissement en arrière-plan (best effort)
- ✅ Pull-to-refresh + bouton manuel

---

## Déploiement sans Mac (TestFlight)

Il faut un Mac + compte Apple Developer (99 €/an) pour publier sur TestFlight ou l’App Store.

---

## Fichiers

```
ios/
  project.yml              # XcodeGen
  PortaSplitMonitor/
    PortaSplitMonitorApp.swift
    ContentView.swift
    Models/StockModels.swift
    Services/
      ClimRadarService.swift
      LocalStoreService.swift
      GeocodingService.swift
      StockMonitor.swift
      NotificationService.swift
      BackgroundRefreshService.swift
      SettingsStore.swift
      AlertStateStore.swift
    Views/
      DashboardView.swift
      SettingsView.swift
    Info.plist
```
