# PortaSplit Monitor — app Expo (SDK 54)

Compatible avec **Expo Go** disponible sur l’App Store (SDK 54).

Même logique que le moniteur Python :
- **Magasin** dans un rayon autour de votre code postal (ex. LM Mérignac)
- **Livraison** en ligne (Darty, Boulanger, Amazon, etc.)
- Source : **ClimRadar**
- Double vérification avant notification

---

## Prérequis

- [Node.js](https://nodejs.org/) 20+
- App **Expo Go** sur iPhone ([App Store](https://apps.apple.com/app/expo-go/id982107779))

---

## Lancer l’app

```powershell
cd mobile
npm.cmd install
npx.cmd expo start
```

> **SDK 54** — compatible avec Expo Go de l’App Store (pas la SDK 57).

1. Scanner le QR code avec l’appareil photo de l’iPhone
2. Ouvrir dans **Expo Go**
3. Autoriser les **notifications**
4. Onglet **Réglages** → code postal `33400`, rayon `100 km`, intervalle `2 min`

---

## Structure

```
mobile/
├── app/                    # Écrans (Expo Router)
│   ├── (tabs)/
│   │   ├── index.tsx       # Stock
│   │   └── settings.tsx    # Réglages
│   └── _layout.tsx
├── src/
│   ├── services/           # ClimRadar, magasins, notifications
│   ├── hooks/
│   └── types.ts
├── app.json
└── package.json
```

---

## Limitation mobile

iOS/Android **ne permettent pas** une surveillance continue en arrière-plan comme sur PC.

| Mode | Fiabilité |
|------|-----------|
| App **ouverte** | ✅ Toutes les 2 min |
| App en arrière-plan | ⚠️ Limité par le système |
| **Moniteur PC + Telegram** | ✅ Recommandé pour 24/7 |

---

## Build standalone (TestFlight)

Pour installer l’app **sans Expo Go** via **TestFlight** :

```powershell
cd mobile
npm.cmd install
npx.cmd eas login
npx.cmd eas init
npx.cmd eas build --platform ios --profile production --auto-submit
```

Guide complet : [`TESTFLIGHT.md`](TESTFLIGHT.md)
