"""Source ClimRadar — API JSON (/api/stock + /api/live)."""



from __future__ import annotations



import math

import time

from dataclasses import dataclass



import requests



CLIMRADAR_PRODUCT_ID = "portasplit"

CLIMRADAR_STOCK_URL = "https://climradar.fr/api/stock"

CLIMRADAR_LIVE_URL = f"https://climradar.fr/api/live?kind=product&id={CLIMRADAR_PRODUCT_ID}"



RETAILER_MAP: dict[str, str] = {

    "leroy-merlin": "leroy_merlin",

    "castorama": "castorama",

    "boulanger": "boulanger",

    "darty": "darty",

    "fnac": "fnac",

    "manomano": "manomano",

    "amazon": "amazon",

}



DELIVERY_RETAILERS = frozenset(

    {"darty", "boulanger", "castorama", "optimea", "amazon", "fnac", "manomano"}

)



_HEADERS = {

    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0",

    "Accept": "application/json",

    "Accept-Language": "fr-FR,fr;q=0.9",

}



_stock_cache: dict | None = None

_stock_cache_at: float = 0.0

_STOCK_CACHE_SEC = 60.0





@dataclass

class ClimRadarOffer:

    seller: str

    retailer_id: str

    in_stock: bool

    price: float | None

    url: str

    area: str

    last_update_min: int | None = None





def _fetch_stock_payload(timeout: int = 60, force: bool = False) -> dict | None:

    global _stock_cache, _stock_cache_at

    now = time.monotonic()

    if not force and _stock_cache and now - _stock_cache_at < _STOCK_CACHE_SEC:

        return _stock_cache



    response = requests.get(CLIMRADAR_STOCK_URL, headers=_HEADERS, timeout=timeout)

    response.raise_for_status()

    payload = response.json()

    if not payload.get("stores") or not payload.get("stockByStore"):

        return None



    _stock_cache = payload

    _stock_cache_at = now

    return payload





def fetch_live_rows(timeout: int = 25) -> list[dict]:

    try:

        response = requests.get(CLIMRADAR_LIVE_URL, headers=_HEADERS, timeout=timeout)

        response.raise_for_status()

        return response.json().get("rows", [])

    except requests.RequestException:

        return []





def product_url_map(live_rows: list[dict]) -> dict[str, str]:

    urls: dict[str, str] = {}

    for row in live_rows:

        product_url = row.get("productUrl") or ""

        if not product_url.startswith("http"):

            continue

        store = row.get("store") or {}

        retailer_id = store.get("retailerId") or ""

        store_id = store.get("id") or ""

        if retailer_id:

            urls[retailer_id] = product_url

        if store_id:

            urls[store_id] = product_url

    return urls





def entry_for_product(entries: list[dict]) -> dict | None:

    for entry in entries:

        if entry.get("productId") == CLIMRADAR_PRODUCT_ID:

            return entry

    return entries[0] if entries else None





def _parse_online_offers(payload: dict, live_rows: list[dict]) -> list[ClimRadarOffer]:

    stores_by_id = {s["id"]: s for s in payload.get("stores", [])}

    retailers_by_id = {r["id"]: r for r in payload.get("retailers", [])}

    product_urls = product_url_map(live_rows)

    offers: list[ClimRadarOffer] = []

    seen: set[str] = set()



    for store_id, entries in payload.get("stockByStore", {}).items():

        store = stores_by_id.get(store_id)

        if not store or store.get("channel") != "online" or store.get("country") != "FR":

            continue



        entry = entry_for_product(entries)

        if not entry:

            continue



        slug = store.get("retailerId") or ""

        retailer_id = RETAILER_MAP.get(slug)

        if not retailer_id or retailer_id in seen:

            continue

        seen.add(retailer_id)



        retailer = retailers_by_id.get(slug, {})

        in_stock = entry.get("status") == "en_stock"

        url = product_urls.get(slug) or product_urls.get(store_id) or ""



        offers.append(

            ClimRadarOffer(

                seller=retailer.get("name") or store.get("name", slug),

                retailer_id=retailer_id,

                in_stock=in_stock,

                price=float(entry["price"]) if entry.get("price") is not None else None,

                url=url,

                area="FR",

                last_update_min=entry.get("lastSeenMinAgo"),

            )

        )



    return offers





def is_climradar_online_available(payload: dict | None = None) -> bool:

    if payload is None:

        try:

            payload = _fetch_stock_payload()

        except requests.RequestException:

            return False

    return bool(payload and payload.get("stores") and payload.get("stockByStore"))





def fetch_climradar_offers(timeout: int = 60) -> list[ClimRadarOffer]:

    payload = _fetch_stock_payload(timeout=timeout)

    if not payload:

        return []

    live_rows = fetch_live_rows(timeout=min(timeout, 25))

    return _parse_online_offers(payload, live_rows)





def get_climradar_stock(retailer_id: str) -> ClimRadarOffer | None:

    for offer in fetch_climradar_offers():

        if offer.retailer_id == retailer_id:

            return offer

    return None





def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:

    r = 6371.0

    p1, p2 = math.radians(lat1), math.radians(lat2)

    dphi = math.radians(lat2 - lat1)

    dlmb = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2

    return 2 * r * math.asin(math.sqrt(a))





def fetch_climradar_stock_payload(timeout: int = 60, force: bool = False) -> dict | None:

    """Expose le dump /api/stock pour local_stores."""

    try:

        return _fetch_stock_payload(timeout=timeout, force=force)

    except requests.RequestException:

        return None


