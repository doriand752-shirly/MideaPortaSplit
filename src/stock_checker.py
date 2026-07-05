from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import replace
from pathlib import Path

import requests
import yaml
from bs4 import BeautifulSoup
from requests import HTTPError

from .browser_fetcher import BrowserFetcher, is_playwright_available
from .climradar import ClimRadarOffer, fetch_climradar_offers
from .models import Retailer, StockResult, StockStatus
from .stealth_fetch import PROTECTED_RETAILER_IDS, fetch_for_retailer, is_bot_blocked

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
                fetch_mode=item.get("fetch_mode", "http"),
            )
        )
    return retailers


def _fetch_http(url: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    from urllib.parse import urlparse

    parsed = urlparse(url)
    headers = {"Referer": f"{parsed.scheme}://{parsed.netloc}/"}
    response = _SESSION.get(url, timeout=timeout, allow_redirects=True, headers=headers)
    response.raise_for_status()
    return response.text


def _fetch_page(
    retailer: Retailer,
    *,
    browser: BrowserFetcher | None = None,
    use_browser: bool = True,
) -> tuple[str, str]:
    """Retourne (html, source) où source = http | browser."""
    mode = retailer.fetch_mode

    if mode == "browser":
        if not use_browser or browser is None:
            raise RuntimeError(
                f"{retailer.name}: mode navigateur requis (playwright install chromium)"
            )
        return browser.fetch(retailer.url), "browser"

    try:
        return _fetch_http(retailer.url), "http"
    except HTTPError as exc:
        if mode == "auto" and exc.response is not None and exc.response.status_code == 403:
            if use_browser and browser is not None:
                return browser.fetch(retailer.url), "browser"
            if use_browser and is_playwright_available():
                with BrowserFetcher() as standalone:
                    return standalone.fetch(retailer.url), "browser"
        raise


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


def _extract_price(html: str, expected_price: float | None = None) -> str | None:
    soup = BeautifulSoup(html, "lxml")
    candidates: list[float] = []

    for selector in (
        "[itemprop='price']",
        "[data-testid='price']",
        ".price",
        ".product-price",
        ".woocommerce-Price-amount",
        "[class*='price']",
    ):
        for element in soup.select(selector):
            content = element.get("content") or element.get_text(" ", strip=True)
            match = PRICE_PATTERN.search(content)
            if match:
                value = float(match.group(1).replace(",", "."))
                candidates.append(value)

    for match in PRICE_PATTERN.finditer(html):
        candidates.append(float(match.group(1).replace(",", ".")))

    if not candidates:
        return None

    if expected_price:
        plausible = [v for v in candidates if v >= expected_price * 0.4]
        if not plausible:
            return None
        best = min(plausible, key=lambda v: abs(v - expected_price))
        return f"{best:.2f} €".replace(".", ",")

    best = max(candidates)
    return f"{best:,.2f}".replace(",", " ").replace(".", ",") + " €"


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

    return StockStatus.UNKNOWN, "Aucun indicateur fiable detecte"


def _extract_amazon_buybox(html: str) -> str:
    patterns = [
        r'id="buybox"[^>]*>(.*?)</div>\s*</div>\s*</div>',
        r'id="desktop_buybox"[^>]*>(.{0,35000})',
        r'id="qualifiedBuybox"[^>]*>(.{0,35000})',
        r'id="apex_desktop"[^>]*>(.{0,35000})',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.IGNORECASE | re.DOTALL)
        if match and len(match.group(1)) > 150:
            return match.group(1)

    cart_match = re.search(r'id="add-to-cart-button"', html, flags=re.IGNORECASE)
    if cart_match:
        start = max(0, cart_match.start() - 10_000)
        end = min(len(html), cart_match.end() + 10_000)
        return html[start:end]
    return ""


def _extract_amazon_availability(html: str) -> str:
    match = re.search(
        r'id="availability"[^>]*>(.*?)</div>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return ""
    text = re.sub(r"<[^>]+>", " ", match.group(1))
    return re.sub(r"\s+", " ", text).strip()


def _amazon_has_buybox_cart(buybox: str) -> bool:
    if not buybox:
        return False
    return bool(
        re.search(
            r'id="add-to-cart-button"|name="submit\.add-to-cart"|id="submit\.add-to-cart"',
            buybox,
            flags=re.IGNORECASE,
        )
    )


def _amazon_cart_disabled(buybox: str) -> bool:
    match = re.search(r"add-to-cart", buybox, flags=re.IGNORECASE)
    if not match:
        return False
    snippet = buybox[max(0, match.start() - 200) : match.end() + 600].lower()
    return bool(re.search(r"disabled|a-button-disabled|aria-disabled=\"true\"", snippet))


def check_amazon(html: str) -> tuple[StockStatus, str]:
    buybox = _extract_amazon_buybox(html)
    availability = _extract_amazon_availability(html)
    avail_lower = availability.lower()
    buybox_lower = buybox.lower()
    page_lower = html.lower()

    out_patterns = [
        r"actuellement indisponible",
        r"currently unavailable",
        r"nous ne savons pas quand",
        r"we don't know when",
        r"temporairement en rupture",
        r"non disponible",
        r"plus disponible",
        r"indisponible",
    ]
    for pattern in out_patterns:
        if re.search(pattern, avail_lower, flags=re.IGNORECASE):
            label = availability[:80] if availability else "indisponible"
            return StockStatus.OUT_OF_STOCK, f"Amazon buybox: {label}"
        if buybox and re.search(pattern, buybox_lower, flags=re.IGNORECASE):
            return StockStatus.OUT_OF_STOCK, "Amazon buybox: indisponible"

    buybox_cart = _amazon_has_buybox_cart(buybox)
    third_party_only = not buybox_cart and bool(
        re.search(
            r"à partir de|autres vendeurs sur amazon|other sellers on amazon|"
            r"all-offers-display|aod-container",
            page_lower,
            flags=re.IGNORECASE,
        )
    )
    if third_party_only:
        return (
            StockStatus.OUT_OF_STOCK,
            "Amazon: revendeurs tiers uniquement (pas le buybox)",
        )

    if buybox_cart:
        if _amazon_cart_disabled(buybox):
            return StockStatus.OUT_OF_STOCK, "Amazon: bouton panier desactive"
        if re.search(r"en stock|in stock", avail_lower, flags=re.IGNORECASE) or re.search(
            r"en stock", buybox_lower, flags=re.IGNORECASE
        ):
            return StockStatus.IN_STOCK, "Amazon buybox: en stock"
        return StockStatus.IN_STOCK, "Amazon buybox: ajouter au panier actif"

    if re.search(r'"isBuyBoxWinner"\s*:\s*true', html, flags=re.IGNORECASE) and re.search(
        r'"maxQuantity"\s*:\s*[1-9]', html
    ):
        return StockStatus.IN_STOCK, "Amazon: buybox gagnant (JSON)"

    if not buybox:
        return StockStatus.UNKNOWN, "Amazon: buybox introuvable"

    return StockStatus.OUT_OF_STOCK, "Amazon buybox: pas de bouton panier"


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
        return StockStatus.OUT_OF_STOCK, "Shopify: epuise"
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


def _apply_price_guards(
    retailer: Retailer,
    status: StockStatus,
    detail: str,
    price: str | None,
) -> tuple[StockStatus, str]:
    if status != StockStatus.IN_STOCK:
        return status, detail

    if retailer.expected_price and price:
        value = _parse_price_value(price)
        if value is not None and value < retailer.expected_price * 0.5:
            return StockStatus.OUT_OF_STOCK, f"Prix trop bas ({price}) — probable faux positif"

    if retailer.max_price and price:
        value = _parse_price_value(price)
        if value is not None and value > retailer.max_price:
            return (
                StockStatus.OUT_OF_STOCK,
                f"Stock revendeur tiers a {price} (max {int(retailer.max_price)} EUR)",
            )

    return status, detail


def _analyze_html(retailer: Retailer, html: str, source: str) -> StockResult:
    status, detail = _detect_stock(retailer, html)
    price = _extract_price(html, retailer.expected_price)
    status, detail = _apply_price_guards(retailer, status, detail, price)
    if source == "browser" and status != StockStatus.ERROR:
        detail = f"{detail} [navigateur]"
    return StockResult(retailer=retailer, status=status, detail=detail, price=price)


def _check_climradar(
    retailer: Retailer,
    offers_by_id: dict[str, ClimRadarOffer],
) -> StockResult:
    offer = offers_by_id.get(retailer.id)
    if not offer:
        return StockResult(
            retailer=retailer,
            status=StockStatus.ERROR,
            detail="Revendeur absent de ClimRadar",
        )

    status = StockStatus.IN_STOCK if offer.in_stock else StockStatus.OUT_OF_STOCK
    price = f"{offer.price:.2f} €".replace(".", ",") if offer.price else None
    retailer_with_url = replace(retailer, url=offer.url or retailer.url)
    label = "en stock" if offer.in_stock else "rupture"
    detail = f"ClimRadar ({label}, MAJ ~10 min)"

    status, detail = _apply_price_guards(retailer_with_url, status, detail, price)
    return StockResult(
        retailer=retailer_with_url,
        status=status,
        detail=detail,
        price=price,
    )


def _merge_climradar_and_direct(
    climradar: StockResult,
    direct: StockResult | None,
) -> StockResult:
    """Fusionne ClimRadar + site revendeur : alerte si l'un des deux confirme le stock."""
    if direct is None or direct.status == StockStatus.ERROR:
        return climradar

    cr_in = climradar.status == StockStatus.IN_STOCK
    dr_in = direct.status == StockStatus.IN_STOCK
    cr_out = climradar.status == StockStatus.OUT_OF_STOCK
    dr_out = direct.status == StockStatus.OUT_OF_STOCK

    if cr_in or dr_in:
        status = StockStatus.IN_STOCK
    elif cr_out and dr_out:
        status = StockStatus.OUT_OF_STOCK
    elif climradar.status == StockStatus.ERROR:
        status = direct.status
    else:
        status = climradar.status

    parts: list[str] = []
    if climradar.status != StockStatus.ERROR:
        cr_label = "en stock" if cr_in else ("rupture" if cr_out else "?")
        parts.append(f"ClimRadar: {cr_label}")
    if direct.status != StockStatus.ERROR:
        parts.append(f"Site: {direct.detail}")
    if (
        climradar.status != StockStatus.ERROR
        and direct.status != StockStatus.ERROR
        and cr_in != dr_in
    ):
        parts.append("sources divergentes")

    price = direct.price or climradar.price
    url = direct.retailer.url or climradar.retailer.url
    retailer = replace(climradar.retailer, url=url)
    detail = " · ".join(parts)
    status, detail = _apply_price_guards(retailer, status, detail, price)
    return StockResult(retailer=retailer, status=status, detail=detail, price=price)


def check_retailer_direct(
    retailer: Retailer,
    *,
    browser: BrowserFetcher | None = None,
    use_browser: bool = True,
) -> StockResult:
    """Vérification directe avec warm-up anti-bot ; repli Playwright si besoin."""
    try:
        html = fetch_for_retailer(retailer.url, retailer.id)
        return _analyze_html(retailer, html, "http")
    except Exception as exc:
        if retailer.id in PROTECTED_RETAILER_IDS and use_browser:
            try:
                if browser is not None:
                    html = browser.fetch(retailer.url)
                elif is_playwright_available():
                    with BrowserFetcher() as standalone:
                        html = standalone.fetch(retailer.url)
                else:
                    raise RuntimeError("Playwright indisponible") from exc
                if is_bot_blocked(html):
                    return StockResult(
                        retailer=retailer,
                        status=StockStatus.ERROR,
                        detail="Anti-bot actif (captcha)",
                    )
                return _analyze_html(retailer, html, "browser")
            except Exception as browser_exc:
                return StockResult(
                    retailer=retailer,
                    status=StockStatus.ERROR,
                    detail=f"Site inaccessible (anti-bot): {browser_exc}",
                )
        return StockResult(
            retailer=retailer,
            status=StockStatus.ERROR,
            detail=str(exc),
        )


def check_retailer(
    retailer: Retailer,
    *,
    browser: BrowserFetcher | None = None,
    use_browser: bool = True,
) -> StockResult:
    try:
        html, source = _fetch_page(retailer, browser=browser, use_browser=use_browser)
    except (requests.RequestException, RuntimeError) as exc:
        return StockResult(
            retailer=retailer,
            status=StockStatus.ERROR,
            detail=str(exc),
        )
    return _analyze_html(retailer, html, source)


def check_all_retailers(
    retailers: list[Retailer],
    *,
    max_workers: int = 6,
    use_browser: bool = True,
) -> list[StockResult]:
    if not retailers:
        return []

    climradar_retailers = [r for r in retailers if r.fetch_mode == "climradar"]
    other_retailers = [r for r in retailers if r.fetch_mode != "climradar"]

    http_retailers = [r for r in other_retailers if r.fetch_mode != "browser"]
    browser_retailers = [r for r in other_retailers if r.fetch_mode == "browser"]
    auto_retailers = [r for r in http_retailers if r.fetch_mode == "auto"]
    plain_http = [r for r in http_retailers if r.fetch_mode == "http"]

    results: list[StockResult] = []

    if climradar_retailers:
        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                climradar_future = executor.submit(fetch_climradar_offers)
                direct_futures = {
                    executor.submit(check_retailer_direct, r, use_browser=False): r
                    for r in climradar_retailers
                }
                offers = climradar_future.result()
                offers_by_id = {o.retailer_id: o for o in offers}
                direct_by_id: dict[str, StockResult] = {}
                for future in as_completed(direct_futures):
                    result = future.result()
                    direct_by_id[result.retailer.id] = result

            need_browser_retry = [
                r
                for r in climradar_retailers
                if direct_by_id.get(r.id) is not None
                and direct_by_id[r.id].status == StockStatus.ERROR
                and r.id in PROTECTED_RETAILER_IDS
            ]
            if need_browser_retry and use_browser and is_playwright_available():
                with BrowserFetcher() as browser:
                    for retailer in need_browser_retry:
                        direct_by_id[retailer.id] = check_retailer_direct(
                            retailer,
                            browser=browser,
                            use_browser=True,
                        )

            for retailer in climradar_retailers:
                cr = _check_climradar(retailer, offers_by_id)
                direct = direct_by_id.get(retailer.id)
                results.append(_merge_climradar_and_direct(cr, direct))
        except requests.RequestException as exc:
            for retailer in climradar_retailers:
                results.append(
                    StockResult(
                        retailer=retailer,
                        status=StockStatus.ERROR,
                        detail=f"ClimRadar indisponible: {exc}",
                    )
                )

    if plain_http:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(check_retailer, r, use_browser=False): r for r in plain_http
            }
            for future in as_completed(futures):
                results.append(future.result())

    need_browser = use_browser and is_playwright_available() and (browser_retailers or auto_retailers)
    if need_browser:
        with BrowserFetcher() as browser:
            for retailer in browser_retailers:
                results.append(check_retailer(retailer, browser=browser, use_browser=True))
            for retailer in auto_retailers:
                results.append(check_retailer(retailer, browser=browser, use_browser=True))
    else:
        for retailer in browser_retailers:
            results.append(
                StockResult(
                    retailer=retailer,
                    status=StockStatus.ERROR,
                    detail="Playwright requis: playwright install chromium",
                )
            )
        for retailer in auto_retailers:
            results.append(check_retailer(retailer, use_browser=False))

    order = {r.id: i for i, r in enumerate(retailers)}
    results.sort(key=lambda item: order.get(item.retailer.id, 999))
    return results
