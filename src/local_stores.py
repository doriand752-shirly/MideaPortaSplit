"""Stock magasin via ClimRadar API JSON (/api/stock)."""

from __future__ import annotations

import html as html_module
import os
import re
from dataclasses import dataclass

import requests

from .climradar import (
    RETAILER_MAP,
    entry_for_product,
    fetch_climradar_stock_payload,
    fetch_live_rows,
    haversine_km,
    product_url_map,
)

DEFAULT_PRODUCT_URL = (
    "https://www.leroymerlin.fr/produits/climatiseur-split-mobile-"
    "reversible-portasplit-midea-par-optimea-93857579.html"
)

BORDER_DEPARTMENTS: dict[str, frozenset[str]] = {
    "33": frozenset({"33", "16", "17", "24", "40", "47", "64", "79", "87"}),
}

_geocode_cache: dict[str, tuple[float, float]] = {}


@dataclass
class LocalStoreStock:
    retailer_slug: str
    retailer_id: str
    retailer_name: str
    store_name: str
    location: str
    postal_code: str
    distance_km: float
    in_stock: bool
    product_url: str
    price: float | None = None
    last_update_min: int | None = None

    @property
    def state_key(self) -> str:
        safe = re.sub(r"[^a-z0-9]+", "-", self.store_name.lower()).strip("-")
        return f"local:{self.retailer_id}:{self.postal_code}:{safe}"


def geocode_postal_code(postal_code: str) -> tuple[float, float, str]:
    if postal_code in _geocode_cache:
        lat, lon = _geocode_cache[postal_code]
        return lat, lon, postal_code[:2]

    response = requests.get(
        "https://api-adresse.data.gouv.fr/search/",
        params={"q": postal_code, "limit": 1},
        timeout=15,
    )
    response.raise_for_status()
    features = response.json().get("features", [])
    if not features:
        raise ValueError(f"Code postal introuvable : {postal_code}")

    props = features[0]["properties"]
    lon, lat = features[0]["geometry"]["coordinates"]
    dept = props.get("depcode") or postal_code[:2]
    _geocode_cache[postal_code] = (lat, lon)
    return lat, lon, dept


def _allowed_departments(postal_code: str) -> frozenset[str]:
    dept = postal_code[:2]
    return BORDER_DEPARTMENTS.get(dept, frozenset({dept}))


def _parse_local_stores(
    payload: dict,
    user_lat: float,
    user_lon: float,
    radius_km: float,
    allowed_depts: frozenset[str],
    live_rows: list[dict],
) -> list[LocalStoreStock]:
    stores_by_id = {s["id"]: s for s in payload.get("stores", [])}
    product_urls = product_url_map(live_rows)
    stores: list[LocalStoreStock] = []
    seen: set[str] = set()

    for store_id, entries in payload.get("stockByStore", {}).items():
        store = stores_by_id.get(store_id)
        if not store or store.get("channel") != "store" or store.get("country") != "FR":
            continue

        slug = store.get("retailerId") or ""
        retailer_id = RETAILER_MAP.get(slug)
        if not retailer_id:
            continue

        entry = entry_for_product(entries)
        if not entry:
            continue

        dept = store.get("department") or (store.get("postalCode") or "")[:2]
        if dept and dept not in allowed_depts:
            continue

        distance = haversine_km(user_lat, user_lon, store["lat"], store["lon"])
        if distance > radius_km:
            continue

        name = html_module.unescape(store.get("name") or "")
        dedupe = f"{retailer_id}:{store.get('postalCode')}:{name}"
        if dedupe in seen:
            continue
        seen.add(dedupe)

        city = html_module.unescape(store.get("city") or "")
        postal = store.get("postalCode") or ""
        location = f"{city.upper()} {postal}" if city else postal
        address = store.get("address") or ""
        product_url = (
            product_urls.get(store_id)
            or product_urls.get(slug)
            or (address if address.startswith("http") else DEFAULT_PRODUCT_URL)
        )

        stores.append(
            LocalStoreStock(
                retailer_slug=slug,
                retailer_id=retailer_id,
                retailer_name=slug,
                store_name=name,
                location=location,
                postal_code=postal,
                distance_km=round(distance, 1),
                in_stock=entry.get("status") == "en_stock",
                product_url=product_url,
                price=float(entry["price"]) if entry.get("price") is not None else None,
                last_update_min=entry.get("lastSeenMinAgo"),
            )
        )

    stores.sort(key=lambda s: (not s.in_stock, s.distance_km))
    return stores


def fetch_local_stores(
    postal_code: str,
    *,
    radius_km: float = 100.0,
    timeout: int = 60,
) -> list[LocalStoreStock]:
    user_lat, user_lon, _ = geocode_postal_code(postal_code)
    allowed_depts = _allowed_departments(postal_code)

    payload = fetch_climradar_stock_payload(timeout=timeout)
    if not payload:
        return []

    live_rows = fetch_live_rows(timeout=min(timeout, 25))
    return _parse_local_stores(payload, user_lat, user_lon, radius_km, allowed_depts, live_rows)


def local_config_from_env() -> tuple[str | None, float]:
    postal = os.getenv("POSTAL_CODE", "").strip()
    if not postal:
        return None, 100.0
    try:
        radius = float(os.getenv("LOCAL_RADIUS_KM", "100"))
    except ValueError:
        radius = 100.0
    return postal, radius
