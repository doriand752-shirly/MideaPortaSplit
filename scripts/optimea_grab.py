"""Surveille Optimea + ManoMano et agit des le retour en stock.

- Optimea (WooCommerce) : ouvre l'URL d'ajout au panier dans TON navigateur
  (l'article atterrit dans ta propre session) + alerte Telegram.
- ManoMano (protege DataDome) : stock lu via ClimRadar, ouvre la page produit
  dans le navigateur + alerte Telegram (pas d'ajout auto possible cote client).

Verification par defaut : toutes les 60 s (evite tout risque de blocage).

Usage :
    python scripts/optimea_grab.py                 # boucle 60s, ouvre le navigateur
    python scripts/optimea_grab.py --interval 90
    python scripts/optimea_grab.py --once          # une passe
    python scripts/optimea_grab.py --no-open        # sans ouvrir le navigateur
    python scripts/optimea_grab.py --only optimea   # une seule cible
"""

from __future__ import annotations

import argparse
import sys
import time
import webbrowser
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.climradar import get_climradar_stock  # noqa: E402
from src.notifiers import send_telegram_text  # noqa: E402

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"
)

OPTIMEA_BASE = "https://www.optimea.fr"
OPTIMEA_PRODUCT_URL = f"{OPTIMEA_BASE}/product/climatiseur-split-mobile-midea/"
OPTIMEA_PRODUCT_ID = 5959

MANOMANO_URL = (
    "https://www.manomano.fr/p/midea-climatiseur-split-mobile-reversible-froid-chaud-"
    "3500w12000btu-wifi-deshumidificateur-ventilateur-jusqua-40m2-kit-fenetre-inclus-83810402"
)


def _load_env() -> None:
    """Charge .env (TELEGRAM_*) sans dependre de python-dotenv."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    import os

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(name.strip(), value)


def notify_telegram(text: str) -> bool:
    import os

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        print("  (Telegram non configure : TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID absents)", flush=True)
        return False
    try:
        send_telegram_text(token, chat_id, text)
        return True
    except requests.RequestException as exc:
        print(f"  (echec Telegram : {exc})", flush=True)
        return False


def optimea_add_to_cart_url(qty: int) -> str:
    return f"{OPTIMEA_PRODUCT_URL}?add-to-cart={OPTIMEA_PRODUCT_ID}&quantity={qty}"


def check_optimea(session: requests.Session) -> tuple[bool, str | None]:
    try:
        resp = session.get(OPTIMEA_PRODUCT_URL, timeout=15)
    except requests.RequestException:
        return False, None
    if not resp.ok:
        return False, None
    low = resp.text.lower()
    if "out-of-stock" in low or "rupture de stock" in low or "outofstock" in low:
        return False, None
    compact = low.replace(" ", "")
    in_stock = (
        "single_add_to_cart_button" in low
        or "schema.org/instock" in low
        or '"availability":"instock"' in compact
        or "in-stock" in low
    )
    return in_stock, None


def check_manomano() -> tuple[bool, str | None]:
    offer = get_climradar_stock("manomano")
    if offer is None:
        return False, None
    return offer.in_stock, (offer.url or MANOMANO_URL)


def handle_optimea(session: requests.Session, qty: int, open_browser: bool) -> None:
    grab_url = optimea_add_to_cart_url(qty)
    if open_browser:
        webbrowser.open(grab_url)
    msg = (
        "🟢 EN STOCK — Optimea\n"
        "Midea PortaSplit (~999 €)\n\n"
        f"Ajouter direct au panier :\n{grab_url}\n\n"
        f"Page produit :\n{OPTIMEA_PRODUCT_URL}\n\n"
        "Commande vite, les stocks partent vite."
    )
    sent = notify_telegram(msg)
    print(f"  Optimea : lien panier ouvert={open_browser}, Telegram={'ok' if sent else 'non'}", flush=True)
    print(f"  {grab_url}", flush=True)


def handle_manomano(url: str, open_browser: bool) -> None:
    if open_browser:
        webbrowser.open(url)
    msg = (
        "🟢 EN STOCK — ManoMano\n"
        "Midea PortaSplit (~999 €)\n\n"
        f"Page produit :\n{url}\n\n"
        "Ajoute au panier depuis le site (ManoMano ne permet pas l'ajout auto)."
    )
    sent = notify_telegram(msg)
    print(f"  ManoMano : page ouverte={open_browser}, Telegram={'ok' if sent else 'non'}", flush=True)
    print(f"  {url}", flush=True)


def run(*, once: bool, interval: int, qty: int, open_browser: bool, only: str | None) -> int:
    _load_env()
    session = requests.Session()
    session.headers.update({"User-Agent": UA, "Accept-Language": "fr-FR,fr;q=0.9"})

    targets = {"optimea", "manomano"}
    if only:
        targets = {only}
    done: set[str] = set()

    while True:
        stamp = time.strftime("%H:%M:%S")
        statuses: list[str] = []

        if "optimea" in targets and "optimea" not in done:
            in_stock, _ = check_optimea(session)
            statuses.append(f"Optimea={'STOCK' if in_stock else 'rupture'}")
            if in_stock:
                print(f"\n[{stamp}] OPTIMEA EN STOCK !", flush=True)
                handle_optimea(session, qty, open_browser)
                done.add("optimea")

        if "manomano" in targets and "manomano" not in done:
            in_stock, url = check_manomano()
            statuses.append(f"ManoMano={'STOCK' if in_stock else 'rupture'}")
            if in_stock:
                print(f"\n[{stamp}] MANOMANO EN STOCK !", flush=True)
                handle_manomano(url or MANOMANO_URL, open_browser)
                done.add("manomano")

        remaining = targets - done
        if not remaining:
            print(f"[{stamp}] Toutes les cibles ont ete signalees. Fin.", flush=True)
            return 0

        print(f"[{stamp}] {' | '.join(statuses)} — prochaine verif dans {interval}s", flush=True)
        if once:
            return 1
        time.sleep(max(interval, 30))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Watcher stock Optimea + ManoMano")
    parser.add_argument("--once", action="store_true", help="Une seule passe")
    parser.add_argument("--interval", type=int, default=60, help="Secondes entre verifs (min 30)")
    parser.add_argument("--qty", type=int, default=1, help="Quantite Optimea")
    parser.add_argument("--no-open", dest="open", action="store_false", help="Ne pas ouvrir le navigateur")
    parser.add_argument("--only", choices=["optimea", "manomano"], help="Surveiller une seule cible")
    parser.set_defaults(open=True)
    args = parser.parse_args(argv)
    return run(
        once=args.once,
        interval=args.interval,
        qty=args.qty,
        open_browser=args.open,
        only=args.only,
    )


if __name__ == "__main__":
    sys.exit(main())
