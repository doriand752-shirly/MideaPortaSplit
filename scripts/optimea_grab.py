"""Ajoute le Midea PortaSplit au panier Optimea des qu'il repasse en stock.

WooCommerce revalide le stock cote serveur : impossible de forcer l'ajout
tant que le produit est en rupture. Ce script surveille la page et, a la
seconde ou le stock revient, tente l'ajout au panier et affiche un lien de
commande direct (cookies de session reutilisables dans le navigateur).

Usage :
    python scripts/optimea_grab.py            # boucle jusqu'au succes
    python scripts/optimea_grab.py --once     # une seule tentative
    python scripts/optimea_grab.py --interval 20 --qty 1 --open
"""

from __future__ import annotations

import argparse
import sys
import time
import webbrowser

import requests

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"
)
BASE = "https://www.optimea.fr"
PRODUCT_URL = f"{BASE}/product/climatiseur-split-mobile-midea/"
PRODUCT_ID = 5959
CART_URL = f"{BASE}/cart/"
CHECKOUT_URL = f"{BASE}/checkout/"


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        }
    )
    return s


def is_in_stock(html: str) -> bool:
    low = html.lower()
    if "out-of-stock" in low or "rupture de stock" in low or "outofstock" in low:
        return False
    compact = low.replace(" ", "")
    if "single_add_to_cart_button" in low:
        return True
    if "schema.org/instock" in low or '"availability":"instock"' in compact:
        return True
    return "in-stock" in low


def try_add_to_cart(session: requests.Session, qty: int) -> bool:
    """Tente l'ajout AJAX puis GET. Retourne True si le panier accepte l'article."""
    session.get(PRODUCT_URL, timeout=15)

    ajax = session.post(
        f"{BASE}/?wc-ajax=add_to_cart",
        data={"product_id": PRODUCT_ID, "quantity": qty},
        headers={"X-Requested-With": "XMLHttpRequest"},
        timeout=15,
    )
    if ajax.ok and '"error":true' not in ajax.text.replace(" ", ""):
        if "fragments" in ajax.text or "cart_hash" in ajax.text:
            return True

    # Repli : ajout via GET classique
    session.get(
        PRODUCT_URL,
        params={"add-to-cart": PRODUCT_ID, "quantity": qty},
        timeout=15,
        allow_redirects=True,
    )
    cart = session.get(CART_URL, timeout=15)
    cl = cart.text.lower()
    empty = (
        "votre panier est vide" in cl
        or "your cart is currently empty" in cl
        or "cart-empty" in cl
    )
    return not empty


def run(*, once: bool, interval: int, qty: int, open_browser: bool) -> int:
    session = _session()
    attempt = 0
    while True:
        attempt += 1
        try:
            resp = session.get(PRODUCT_URL, timeout=15)
            in_stock = resp.ok and is_in_stock(resp.text)
        except requests.RequestException as exc:
            print(f"[{attempt}] erreur reseau : {exc}", flush=True)
            in_stock = False

        stamp = time.strftime("%H:%M:%S")
        if in_stock:
            print(f"[{stamp}] EN STOCK — tentative d'ajout au panier...", flush=True)
            if try_add_to_cart(session, qty):
                print("\n===> AJOUTE AU PANIER !", flush=True)
                print(f"Panier   : {CART_URL}")
                print(f"Commande : {CHECKOUT_URL}")
                cookies = "; ".join(f"{k}={v}" for k, v in session.cookies.get_dict().items())
                if cookies:
                    print("\nCookies de session (a coller dans le navigateur si besoin) :")
                    print(cookies)
                if open_browser:
                    webbrowser.open(CHECKOUT_URL)
                return 0
            print(f"[{stamp}] ajout refuse (stock repasse indisponible ?)", flush=True)
        else:
            print(f"[{stamp}] rupture — nouvelle verif dans {interval}s", flush=True)

        if once:
            return 1
        time.sleep(max(interval, 5))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Auto add-to-cart Optimea PortaSplit")
    parser.add_argument("--once", action="store_true", help="Une seule tentative")
    parser.add_argument("--interval", type=int, default=15, help="Secondes entre verifs")
    parser.add_argument("--qty", type=int, default=1, help="Quantite")
    parser.add_argument("--open", action="store_true", help="Ouvrir la commande dans le navigateur")
    args = parser.parse_args(argv)
    return run(once=args.once, interval=args.interval, qty=args.qty, open_browser=args.open)


if __name__ == "__main__":
    sys.exit(main())
