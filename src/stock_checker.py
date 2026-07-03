from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
import yaml
from bs4 import BeautifulSoup

from .models import Retailer, StockResult, StockStatus

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

DEFAULT_TIMEOUT = 12

OUT_OF_STOCK_PATTERNS = [
    r"rupture\s+de\s+stock",
    r"temporairement\s+indisponible",
    r"plus\s+propos[ée]\s+à\s+la\s+vente",
    r"produit\s+indisponible",
    r"article\s+indisponible",
    r"non\s+disponible",
    r"épuisé",
    r"epuise",
    r"out\s*of\s*stock",
    r"currently\s+unavailable",
    r"indisponible\s+en\s+ligne",
    r"stock\s+épuisé",
    r"en\s+rupture",
    r"sold\s*out",
    r"outofstock",
    r"schema\.org/outofstock",
    r'"availability"\s*:\s*"[^"]*outofstock',
    r'"availability"\s*:\s*"https?://schema\.org/outofstock"',
]

IN_STOCK_PATTERNS = [
    r"ajouter\s+au\s+panier",
    r"ajouter\s+au\s+caddie",
    r"acheter\s+maintenant",
    r"en\s+stock",
    r"disponible\s+en\s+ligne",
    r"schema\.org/instock",
    r'"availability"\s*:\s*"[^"]*instock',
    r'"availability"\s*:\s*"https?://schema\.org/instock"',
    r"add-to-cart",
    r"addtocart",
    r"data-testid=[\"']add-to-cart",
]

PRICE_PATTERN = re.compile(r"(\d{1,4}(?:[.,]\d{2})?)\s*€")

_SESSION = requests.Session()
_SESSION.headers.update(
    {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    }
)


def load_retailers(config_path: Path) -> list[Retailer]:
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    retailers = []
    for item in data.get("retailers", []):
        if not item.get("enabled", True):
            continue
        retailers.append(
            Retailer(
                id=item["id"],
                name=item["name"],
                url=item["url"],
                expected_price=item.get("expected_price"),
                max_price=item.get("max_price"),
                enabled=True,
                checker=item.get("checker", "generic"),
            )
        )
    return retailers


def _fetch(url: str, timeout: int = DEFAULT_TIMEOUT) -> tuple[int, str]:
    from urllib.parse import urlparse

    parsed = urlparse(url)
    headers = {"Referer": f"{parsed.scheme}://{parsed.netloc}/"}
    response = _SESSION.get(url, timeout=timeout, allow_redirects=True, headers=headers)
    response.raise_for_status()
    return response.status_code, response.text


def _extract_json_ld_availability(html: str) -> StockStatus | None:
    soup = BeautifulSoup(html, "lxml")
    for script in soup.find_all("script", type="application/ld+json"):
        raw = script.string or script.get_text()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue

        items = payload if isinstance(payload, list) else [payload]
        for item in items:
            offers = item.get("offers")
            if isinstance(offers, list):
                offer_list = offers
            elif isinstance(offers, dict):
                offer_list = [offers]
            else:
                continue

            for offer in offer_list:
                availability = str(offer.get("availability", "")).lower()
                if "instock" in availability:
                    return StockStatus.IN_STOCK
                if "outofstock" in availability:
                    return StockStatus.OUT_OF_STOCK
    return None


def _extract_price(html: str) -> str | None:
    soup = BeautifulSoup(html, "lxml")
    for selector in (
        "[itemprop='price']",
        "[data-testid='price']",
        ".price",
        ".product-price",
        ".woocommerce-Price-amount",
    ):
        element = soup.select_one(selector)
        if element:
            content = element.get("content") or element.get_text(" ", strip=True)
            match = PRICE_PATTERN.search(content)
            if match:
                return f"{match.group(1).replace('.', ',')} €"

    match = PRICE_PATTERN.search(html)
    if match:
        return f"{match.group(1).replace('.', ',')} €"
    return None


def _normalize_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text(" ", strip=True).lower()


def _match_any(patterns: list[str], text: str) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(0)
    return None


def detect_stock_from_html(html: str) -> tuple[StockStatus, str]:
    text = _normalize_text(html)
    compact = re.sub(r"\s+", " ", html.lower())

    negative = _match_any(OUT_OF_STOCK_PATTERNS, text) or _match_any(
        OUT_OF_STOCK_PATTERNS, compact
    )
    if negative:
        return StockStatus.OUT_OF_STOCK, f"Indicateur: « {negative} »"

    json_ld_status = _extract_json_ld_availability(html)
    if json_ld_status is not None:
        return json_ld_status, "JSON-LD schema.org"

    positive = _match_any(IN_STOCK_PATTERNS, text) or _match_any(
        IN_STOCK_PATTERNS, compact
    )

    if positive:
        return StockStatus.IN_STOCK, f"Indicateur: « {positive} »"

    return StockStatus.UNKNOWN, "Aucun indicateur fiable détecté"


def check_amazon(html: str) -> tuple[StockStatus, str]:
    compact = html.lower()
    if "actuellement indisponible" in compact or "currently unavailable" in compact:
        return StockStatus.OUT_OF_STOCK, "Amazon: actuellement indisponible"
    if "voir les options d'achat" in compact and "ajouter au panier" not in compact:
        return StockStatus.OUT_OF_STOCK, "Amazon: revendeurs tiers uniquement"
    if re.search(r"en stock.{0,80}ajouter au panier", compact):
        return StockStatus.IN_STOCK, "Amazon: en stock"
    if "ajouter au panier" in compact and "indisponible" not in compact:
        return StockStatus.IN_STOCK, "Amazon: ajouter au panier"
    return detect_stock_from_html(html)


def check_woocommerce(html: str) -> tuple[StockStatus, str]:
    compact = html.lower()
    if "out-of-stock" in compact or "stock out-of-stock" in compact:
        return StockStatus.OUT_OF_STOCK, "WooCommerce: rupture de stock"
    if "in-stock" in compact and "single_add_to_cart_button" in compact:
        if "disabled" not in compact.split("single_add_to_cart_button")[1][:200]:
            return StockStatus.IN_STOCK, "WooCommerce: ajout au panier actif"
    return detect_stock_from_html(html)


def check_shopify(html: str) -> tuple[StockStatus, str]:
    compact = html.lower()
    if '"available":false' in compact.replace(" ", ""):
        return StockStatus.OUT_OF_STOCK, "Shopify: available=false"
    if '"available":true' in compact.replace(" ", ""):
        return StockStatus.IN_STOCK, "Shopify: available=true"
    if "épuisé" in compact or "sold out" in compact:
        return StockStatus.OUT_OF_STOCK, "Shopify: épuisé"
    if "ajouter au panier" in compact:
        return StockStatus.IN_STOCK, "Shopify: ajouter au panier"
    return detect_stock_from_html(html)


def _detect_stock(retailer: Retailer, html: str) -> tuple[StockStatus, str]:
    checkers = {
        "amazon": check_amazon,
        "woocommerce": check_woocommerce,
        "shopify": check_shopify,
    }
    checker = checkers.get(retailer.checker, detect_stock_from_html)
    return checker(html)


def _parse_price_value(price: str | None) -> float | None:
    if not price:
        return None
    match = re.search(r"(\d+(?:[.,]\d+)?)", price.replace(" ", ""))
    if not match:
        return None
    return float(match.group(1).replace(",", "."))


def check_retailer(retailer: Retailer) -> StockResult:
    try:
        _, html = _fetch(retailer.url)
    except requests.RequestException as exc:
        return StockResult(
            retailer=retailer,
            status=StockStatus.ERROR,
            detail=str(exc),
        )

    status, detail = _detect_stock(retailer, html)
    price = _extract_price(html)

    if (
        status == StockStatus.IN_STOCK
        and retailer.expected_price
        and price
    ):
        value = _parse_price_value(price)
        if value is not None and value < retailer.expected_price * 0.5:
            status = StockStatus.OUT_OF_STOCK
            detail = f"Prix trop bas ({price}) — probable faux positif"

    if (
        status == StockStatus.IN_STOCK
        and retailer.max_price
        and price
    ):
        value = _parse_price_value(price)
        if value is not None and value > retailer.max_price:
            status = StockStatus.OUT_OF_STOCK
            detail = f"Stock revendeur tiers a {price} (max {int(retailer.max_price)} EUR)"

    return StockResult(retailer=retailer, status=status, detail=detail, price=price)


def check_all_retailers(
    retailers: list[Retailer],
    *,
    max_workers: int = 6,
) -> list[StockResult]:
    if not retailers:
        return []

    results: list[StockResult] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(check_retailer, r): r for r in retailers}
        for future in as_completed(futures):
            results.append(future.result())

    order = {r.id: i for i, r in enumerate(retailers)}
    results.sort(key=lambda item: order.get(item.retailer.id, 999))
    return results
