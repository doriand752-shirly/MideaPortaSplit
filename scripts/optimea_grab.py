"""Surveille Optimea + ManoMano et alerte des le retour en stock.

- Optimea (WooCommerce) : verification depuis votre IP + alerte Telegram
  avec le lien d'ajout au panier (?add-to-cart=5959). Voir OPTIMEA.md.
- ManoMano : stock lu via ClimRadar + alerte Telegram.

Verification par defaut : toutes les 60 s.

Usage :
    python scripts/optimea_grab.py --only optimea
    python scripts/optimea_grab.py --interval 90
    python scripts/optimea_grab.py --once
    python scripts/optimea_grab.py
"""

from __future__ import annotations

import argparse
import re
import sys
import time
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


_PRICE_RE = re.compile(r"(\d{1,4}(?:[.,]\d{2})?)\s*€")


def _extract_optimea_price(html: str) -> str | None:
    # Le prix WooCommerce (999,00 &nbsp; <span>€</span>) casse le regex direct :
    # on lit le prix fiable du JSON-LD / meta ("price": "999.00").
    m = re.search(r'"price"\s*:\s*"?(\d+(?:[.,]\d+)?)"?', html)
    if not m:
        m = re.search(r'itemprop=["\']price["\'][^>]*content=["\'](\d+(?:[.,]\d+)?)', html)
    if not m:
        return None
    value = float(m.group(1).replace(",", "."))
    return f"{value:.2f} €".replace(".", ",")


def _optimea_signals(html: str) -> str:
    """Compteurs de signaux stock bruts (comme la sonde de diagnostic)."""
    low = html.lower()
    counts = {
        "outofstock": low.count("outofstock") + low.count("out-of-stock"),
        "instock": low.count("instock") + low.count("in-stock"),
        "backorder": low.count("backorder"),
        "on-backorder": low.count("on-backorder"),
        "stock_status": low.count("stock_status"),
    }
    has_variations = 'data-product_variations="' in low
    parts = [f"{k}={v}" for k, v in counts.items()]
    parts.append(f"variations={has_variations}")
    return " ".join(parts)


def check_optimea(session: requests.Session) -> tuple[bool, str | None, str]:
    """Retourne (en_stock, url, detail)."""
    try:
        resp = session.get(OPTIMEA_PRODUCT_URL, timeout=15)
    except requests.RequestException as exc:
        return False, None, f"erreur reseau ({exc.__class__.__name__})"
    if not resp.ok:
        return False, None, f"HTTP {resp.status_code}"
    low = resp.text.lower()
    price = _extract_optimea_price(resp.text)
    price_txt = f", {price}" if price else ""
    signals = _optimea_signals(resp.text)
    if "out-of-stock" in low or "rupture de stock" in low or "outofstock" in low:
        return False, None, f"rupture{price_txt} [{signals}]"
    compact = low.replace(" ", "")
    in_stock = (
        "single_add_to_cart_button" in low
        or "schema.org/instock" in low
        or '"availability":"instock"' in compact
        or "in-stock" in low
    )
    label = "EN STOCK" if in_stock else "statut indetermine"
    return in_stock, None, f"{label}{price_txt} [{signals}]"


def check_manomano() -> tuple[bool, str | None, str]:
    """Retourne (en_stock, url, detail) via ClimRadar."""
    offer = get_climradar_stock("manomano")
    if offer is None:
        return False, None, "absent de ClimRadar"
    price_txt = f", {offer.price:.2f} €".replace(".", ",") if offer.price else ""
    freshness = ""
    if offer.last_update_min is not None:
        freshness = f", MAJ il y a {offer.last_update_min} min"
    label = "EN STOCK" if offer.in_stock else "rupture"
    detail = f"{label}{price_txt}{freshness} (ClimRadar)"
    return offer.in_stock, (offer.url or MANOMANO_URL), detail


def handle_optimea(qty: int, detail: str) -> None:
    stamp = time.strftime("%d/%m %H:%M:%S")
    grab_url = optimea_add_to_cart_url(qty)
    msg = (
        "🟢 EN STOCK — Optimea\n"
        "Midea PortaSplit (~999 €)\n\n"
        f"Detecte le {stamp}\n"
        f"Detail : {detail}\n\n"
        f"Ajouter direct au panier :\n{grab_url}\n\n"
        f"Page produit :\n{OPTIMEA_PRODUCT_URL}\n\n"
        "Commande vite, les stocks partent vite."
    )
    sent = notify_telegram(msg)
    print(f"  Detail capture : {detail}", flush=True)
    print(f"  Optimea : Telegram={'ok' if sent else 'non'}", flush=True)
    print(f"  Lien panier : {grab_url}", flush=True)


def handle_manomano(url: str, detail: str) -> None:
    stamp = time.strftime("%d/%m %H:%M:%S")
    msg = (
        "🟢 EN STOCK — ManoMano\n"
        "Midea PortaSplit (~999 €)\n\n"
        f"Detecte le {stamp}\n"
        f"Detail : {detail}\n\n"
        f"Page produit :\n{url}"
    )
    sent = notify_telegram(msg)
    print(f"  Detail capture : {detail}", flush=True)
    print(f"  ManoMano : Telegram={'ok' if sent else 'non'}", flush=True)
    print(f"  {url}", flush=True)


def run(*, once: bool, interval: int, qty: int, only: str | None) -> int:
    _load_env()
    session = requests.Session()
    session.headers.update({"User-Agent": UA, "Accept-Language": "fr-FR,fr;q=0.9"})

    targets = {"optimea", "manomano"}
    if only:
        targets = {only}
    # Alerte sur transition (rupture -> stock) pour eviter de spammer chaque minute.
    alerted: set[str] = set()

    while True:
        stamp = time.strftime("%H:%M:%S")
        statuses: list[str] = []

        if "optimea" in targets:
            in_stock, _, detail = check_optimea(session)
            statuses.append(f"Optimea: {detail}")
            if in_stock and "optimea" not in alerted:
                print(f"\n[{stamp}] OPTIMEA EN STOCK !", flush=True)
                handle_optimea(qty, detail)
                alerted.add("optimea")
            elif not in_stock:
                alerted.discard("optimea")

        if "manomano" in targets:
            in_stock, url, detail = check_manomano()
            statuses.append(f"ManoMano: {detail}")
            if in_stock and "manomano" not in alerted:
                print(f"\n[{stamp}] MANOMANO EN STOCK !", flush=True)
                handle_manomano(url or MANOMANO_URL, detail)
                alerted.add("manomano")
            elif not in_stock:
                alerted.discard("manomano")

        print(f"[{stamp}] {' | '.join(statuses)} — prochaine verif dans {interval}s", flush=True)
        if once:
            return 0
        time.sleep(max(interval, 30))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Watcher stock Optimea + ManoMano")
    parser.add_argument("--once", action="store_true", help="Une seule passe")
    parser.add_argument("--interval", type=int, default=60, help="Secondes entre verifs (min 30)")
    parser.add_argument("--qty", type=int, default=1, help="Quantite Optimea")
    parser.add_argument("--only", choices=["optimea", "manomano"], help="Surveiller une seule cible")
    args = parser.parse_args(argv)
    return run(
        once=args.once,
        interval=args.interval,
        qty=args.qty,
        only=args.only,
    )


if __name__ == "__main__":
    sys.exit(main())
