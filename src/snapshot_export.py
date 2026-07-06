"""Export JSON snapshot for the mobile app (GitHub Actions -> raw.githubusercontent.com)."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .availability import ActionableOffer, DELIVERY_ONLINE_RETAILERS
from .local_stores import BORDER_DEPARTMENTS, LocalStoreStock
from .models import StockResult, StockStatus

BORDER_DEPARTMENT_LABELS: dict[str, str] = {
    "33": "Gironde",
    "16": "Charente",
    "17": "Charente-Maritime",
    "24": "Dordogne",
    "40": "Landes",
    "47": "Lot-et-Garonne",
    "64": "Pyrénées-Atlantiques",
    "79": "Deux-Sèvres",
    "87": "Haute-Vienne",
}

SNAPSHOT_VERSION = 1
SNAPSHOT_HEARTBEAT_FIELD = "lastHeartbeatDate"
SNAPSHOT_ALERT_DATES_FIELD = "alertDates"
SNAPSHOT_STOCK_STATE_FIELD = "stockState"


def _parse_price(raw: str | None) -> float | None:
    if not raw:
        return None
    match = re.search(r"(\d+(?:[.,]\d+)?)", raw.replace("\u00a0", " "))
    if not match:
        return None
    return float(match.group(1).replace(",", "."))


def _department_labels(postal_code: str) -> list[str]:
    dept = postal_code[:2]
    allowed = BORDER_DEPARTMENTS.get(dept, frozenset({dept}))
    return [BORDER_DEPARTMENT_LABELS.get(d, f"Dép. {d}") for d in sorted(allowed)]


def _online_offer(result: StockResult) -> dict[str, Any]:
    in_stock = result.status == StockStatus.IN_STOCK
    delivery = in_stock and result.retailer.id in DELIVERY_ONLINE_RETAILERS
    detail = result.detail or ""
    sources: list[str] = []
    if "ClimRadar" in detail or "climradar" in detail.lower():
        sources.append("climradar")
    if "Site" in detail or "direct" in detail.lower() or result.retailer.fetch_mode != "climradar":
        sources.append("direct")
    if not sources:
        sources = ["climradar" if result.retailer.fetch_mode == "climradar" else "direct"]

    return {
        "id": result.retailer.id,
        "retailerName": result.retailer.name,
        "inStock": in_stock,
        "price": _parse_price(result.price),
        "url": result.retailer.url,
        "deliveryEligible": delivery and result.retailer.id != "leroy_merlin",
        "lastUpdateMin": None,
        "sources": sources,
        "sourceDetail": detail or "Moniteur GitHub Actions",
        "checkError": result.status == StockStatus.ERROR,
    }


def _local_store(store: LocalStoreStock) -> dict[str, Any]:
    safe = re.sub(r"[^a-z0-9]+", "-", store.store_name.lower()).strip("-")
    return {
        "id": f"local:{store.retailer_id}:{store.postal_code}:{safe}",
        "storeName": store.store_name,
        "retailerId": store.retailer_id,
        "location": store.location,
        "postalCode": store.postal_code,
        "department": store.postal_code[:2],
        "distanceKm": store.distance_km,
        "inStock": store.in_stock,
        "price": int(store.price) if store.price else None,
        "productURL": store.product_url,
        "lastUpdateMin": store.last_update_min,
        "stockSource": "climradar",
    }


def _actionable(offer: ActionableOffer) -> dict[str, Any]:
    price: float | None = None
    if offer.price:
        price = _parse_price(offer.price)
    elif offer.store and offer.store.price:
        price = float(offer.store.price)

    offer_id = offer.state_key
    if offer.kind == "livraison" and not offer_id.startswith("livraison:"):
        offer_id = f"livraison:{offer.retailer_id}"

    return {
        "id": offer_id,
        "kind": offer.kind,
        "title": offer.retailer_name,
        "detail": offer.detail,
        "url": offer.url,
        "price": price,
    }


def build_snapshot(
    *,
    online_results: list[StockResult],
    local_stores: list[LocalStoreStock],
    actionable: list[ActionableOffer],
    postal_code: str,
    radius_km: float,
    last_heartbeat_date: str | None = None,
    alert_dates: dict[str, str] | None = None,
    stock_state: dict[str, str] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schemaVersion": SNAPSHOT_VERSION,
        "checkedAt": datetime.now(timezone.utc).isoformat(),
        "postalCode": postal_code,
        "radiusKm": radius_km,
        "monitoredDepartments": _department_labels(postal_code),
        "onlineOffers": [_online_offer(r) for r in online_results],
        "localStores": [_local_store(s) for s in local_stores],
        "actionable": [_actionable(o) for o in actionable],
        "dataMode": "cloud",
        "climradarAvailable": True,
        "source": "github-actions",
    }
    if last_heartbeat_date:
        payload[SNAPSHOT_HEARTBEAT_FIELD] = last_heartbeat_date
    if alert_dates:
        payload[SNAPSHOT_ALERT_DATES_FIELD] = alert_dates
    if stock_state:
        payload[SNAPSHOT_STOCK_STATE_FIELD] = stock_state
    return payload


def write_snapshot(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
