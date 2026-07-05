# Publier sur TestFlight (Expo EAS)

Guide pas à pas pour installer **PortaSplit Monitor** sur votre iPhone via **TestFlight**, sans Mac.

---

## Prérequis

| Élément | Détail |
|---------|--------|
| **Apple Developer** | Compte payant (99 €/an) — [developer.apple.com](https://developer.apple.com) |
| **Compte Expo** | Gratuit — [expo.dev/signup](https://expo.dev/signup) |
| **Git** | Recommandé (EAS Build l’utilise pour empaqueter le code) |

---

## Étape 1 — Compte Apple Developer

1. Inscrivez-vous au [Apple Developer Program](https://developer.apple.com/programs/)
2. Notez votre **Team ID** : [developer.apple.com/account](https://developer.apple.com/account) → Membership → **Team ID** (10 caractères, ex. `AB12CD34EF`)

---

## Étape 2 — App Store Connect

1. Allez sur [appstoreconnect.apple.com](https://appstoreconnect.apple.com)
2. **Apps** → **+** → **Nouvelle app**
3. Renseignez :
   - **Nom** : PortaSplit Monitor
   - **Langue principale** : Français
   - **Bundle ID** : créez `fr.portasplit.monitor` (ou changez-le dans `app.json` si déjà pris)
   - **SKU** : `portasplit-monitor` (identifiant interne, libre)
4. Notez l’**Apple ID de l’app** (nombre à 10 chiffres) : App Store Connect → votre app → **Informations sur l’app** → **Identifiant Apple**

---

## Étape 3 — Configurer EAS localement

```powershell
cd mobile
npm.cmd install
npx.cmd eas login
npx.cmd eas init
```

`eas init` va :
- Créer le projet sur expo.dev
- Remplacer `projectId` et `owner` dans `app.json`

Ensuite, éditez `eas.json` si besoin :

```json
"appleTeamId": "2QKC854C2J"
```

L’**ascAppId** (identifiant numérique App Store Connect) est **optionnel** : laissez-le vide et `eas submit` vous proposera de sélectionner l’app. Pour l’auto-submit, ajoutez-le une fois l’app créée dans App Store Connect → **Informations sur l’app** → **Identifiant Apple** (10 chiffres).

---

## Étape 4 — Build iOS (cloud, depuis Windows)

```powershell
npx.cmd eas build --platform ios --profile production
```

- EAS demande vos identifiants Apple (ou une clé API `.p8` — recommandé)
- Le build tourne sur les serveurs Expo (~15–25 min)
- Vous recevez un lien vers le `.ipa` une fois terminé

**Première fois** : EAS propose de créer les certificats et profils de provisioning automatiquement → acceptez.

### Clé API Apple (recommandé)

1. [appstoreconnect.apple.com](https://appstoreconnect.apple.com) → **Utilisateurs et accès** → **Intégrations** → **Clés API**
2. Créez une clé avec rôle **Admin** ou **App Manager**
3. Téléchargez le fichier `.p8` (une seule fois)
4. Lors du build/submit, EAS vous demandera : Key ID, Issuer ID, fichier `.p8`

---

## Étape 5 — Envoyer sur TestFlight

### Option A — Automatique après le build

Relancez le build avec soumission :

```powershell
npx.cmd eas build --platform ios --profile production --auto-submit
```

### Option B — Soumettre le dernier build

```powershell
npm.cmd run submit:ios
```

ou :

```powershell
npx.cmd eas submit --platform ios --profile production --latest
```

---

## Étape 6 — Inviter des testeurs

1. App Store Connect → votre app → **TestFlight**
2. Attendez la fin du traitement Apple (~5–30 min, parfois plus la 1ère fois)
3. Remplissez **Conformité exportation** si demandé → choisissez **Non** (chiffrement standard HTTPS uniquement, déjà déclaré dans `app.json`)
4. **Testeurs internes** : membres de votre équipe Apple Developer (accès immédiat)
5. **Testeurs externes** : ajoutez des e-mails → Apple valide la build (~24–48 h la 1ère fois)

Sur iPhone : installez **TestFlight** depuis l’App Store, acceptez l’invitation par e-mail.

---

## Commandes utiles

```powershell
# Statut du dernier build
npx.cmd eas build:list --platform ios

# Nouvelle version (incrémente automatiquement le build number)
npx.cmd eas build --platform ios --profile production

# Voir les credentials Apple gérés par EAS
npx.cmd eas credentials --platform ios
```

---

## Changer le Bundle ID

Si `fr.portasplit.monitor` est indisponible, modifiez dans `app.json` :

```json
"bundleIdentifier": "fr.votrenom.portasplit"
```

Recréez l’app dans App Store Connect avec le même Bundle ID.

---

## Limitations TestFlight

- Builds TestFlight expirent après **90 jours**
- Max **100 testeurs externes** (10 000 avec review Apple)
- La surveillance en arrière-plan reste limitée par iOS — gardez le moniteur PC + Telegram pour du 24/7 fiable

---

## Dépannage

| Problème | Solution |
|----------|----------|
| Bundle ID déjà utilisé | Changez le `bundleIdentifier` dans `app.json` |
| Erreur certificats | `eas credentials --platform ios` → reset |
| Build rejeté (export compliance) | `ITSAppUsesNonExemptEncryption: false` déjà dans `app.json` |
| Pas de notifications | Autorisez les notifs au 1er lancement de l’app |

---

## Coûts

- Apple Developer : **99 €/an**
- EAS Build : plan gratuit Expo = builds limités/mois ; [expo.dev/pricing](https://expo.dev/pricing)
