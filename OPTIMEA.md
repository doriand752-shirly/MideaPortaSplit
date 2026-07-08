# Optimea — surveillance locale & ajout au panier

Le **Midea PortaSplit** revient parfois en stock chez [Optimea](https://www.optimea.fr/product/climatiseur-split-mobile-midea/) (~999 €), le distributeur officiel. Les stocks partent en quelques minutes : il faut être **plus rapide que le moniteur cloud**.

## En bref

| | Moniteur cloud (GitHub Actions) | Watcher local (votre PC) |
|---|---|---|
| Optimea | Bloqué (403 — IP datacenter) | Fonctionne (IP résidentielle) |
| Fréquence | ~10 min | **60 s** (configurable) |
| Alerte | Telegram / ntfy | Telegram |
| Ajout panier | — | **Lien direct** dans le message |

**→ Lancez le watcher sur votre PC quand vous attendez un restock Optimea.**

---

## Lien magique : ajouter au panier en 1 clic

Optimea utilise WooCommerce. Pas besoin de cliquer sur le site : ouvrez cette URL **dans votre navigateur** (connecté à votre compte Optimea ou en invité) :

**https://www.optimea.fr/product/climatiseur-split-mobile-midea/?add-to-cart=5959&quantity=1**

- `5959` = identifiant produit WooCommerce
- L'article est ajouté à **votre** session navigateur
- Ensuite : panier → paiement (le stock peut partir entre-temps, allez vite)

> Gardez ce lien en favori. Dès qu'une alerte Telegram arrive, cliquez dessus.

---

## Watcher local (recommandé)

Script : [`scripts/optimea_grab.py`](scripts/optimea_grab.py)

### Prérequis (une fois)

```powershell
cd MideaPortaSplit
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Dans `.env`, renseignez au minimum :

```env
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

(Voir [README — Configuration Telegram](README.md#configuration-telegram) pour créer le bot.)

### Lancer la surveillance Optimea

```powershell
python scripts/optimea_grab.py --only optimea
```

Vérification **toutes les 60 secondes**. La console affiche le détail du stock à chaque cycle, par ex. :

```
[18:21:04] Optimea: rupture, 999,00 € [outofstock=3 instock=0 ...] — prochaine verif dans 60s
```

### Dès que c'est en stock

1. Message **Telegram** avec le lien panier et le détail technique
2. Même info dans la **console**
3. Le script **continue** de tourner (pas d'arrêt automatique)
4. Une seule alerte par retour en stock (anti-spam) ; si ça repasse en rupture puis revient, nouvelle alerte

### Options utiles

```powershell
# Une seule vérification (test)
python scripts/optimea_grab.py --only optimea --once

# Toutes les 90 s au lieu de 60
python scripts/optimea_grab.py --only optimea --interval 90

# Optimea + ManoMano
python scripts/optimea_grab.py
```

---

## Schéma

```
┌─────────────────────┐         ┌──────────────────────┐
│  GitHub Actions     │         │  Votre PC            │
│  (cloud, 24/7)      │         │  (watcher local)     │
├─────────────────────┤         ├──────────────────────┤
│ Darty, Amazon, …    │         │ Optimea toutes les   │
│ Magasins, snapshot  │         │ 60 s + lien panier   │
│ Optimea → 403 ❌    │         │ Telegram ✅          │
└─────────────────────┘         └──────────────────────┘
         │                                │
         └──────── complémentaires ───────┘
              (ne remplacent pas l'autre)
```

Le cloud couvre le reste des revendeurs et alimente le [tableau de bord web](https://doriand752-shirly.github.io/MideaPortaSplit/). Le watcher local comble le trou Optimea.

---

## FAQ

**Pourquoi GitHub ne suffit pas pour Optimea ?**  
Optimea bloque les IP de datacenters (dont GitHub Actions). Depuis chez vous, la page répond normalement.

**Le lien panier ouvre-t-il automatiquement le navigateur ?**  
Non — vous recevez le lien par Telegram et vous cliquez quand vous êtes prêt.

**Et si je n'ai pas Telegram ?**  
Le lien panier ci-dessus + rafraîchir la page produit manuellement. Le watcher sans `.env` affiche quand même l'état dans la console.

**Le stock affiché est-il fiable ?**  
Optimea ne publie pas toujours une quantité exacte. Le script lit les signaux WooCommerce (`instock`, `outofstock`, etc.) — en cas de doute, testez le lien panier tout de suite.

**C'est légal / autorisé ?**  
Vous interrogez une page publique à la même fréquence qu'un humain patient (60 s). Pas de contournement de paiement : vous commandez vous-même sur le site.

---

## Liens

- Page produit : https://www.optimea.fr/product/climatiseur-split-mobile-midea/
- Ajout panier : https://www.optimea.fr/product/climatiseur-split-mobile-midea/?add-to-cart=5959&quantity=1
- Tableau de bord stock (tous revendeurs) : https://doriand752-shirly.github.io/MideaPortaSplit/
