"""Double verification du stock avant envoi d'une alerte."""

from __future__ import annotations

import os
import time

from .availability import ActionableOffer, delivery_available_online
from .local_stores import fetch_local_stores
from .stock_checker import check_all_retailers
from .models import Retailer


def _confirm_enabled() -> bool:
    return os.getenv("CONFIRM_STOCK", "true").strip().lower() in ("1", "true", "yes", "on")


def confirm_local_store(
    offer: ActionableOffer,
    postal_code: str,
    radius_km: float,
) -> bool:
    """Deux lectures ClimRadar : le magasin doit etre en stock aux deux."""
    if not offer.store:
        return False

    target_key = offer.state_key
    checks = 0
    for _ in range(2):
        stores = fetch_local_stores(postal_code, radius_km=radius_km)
        if any(s.state_key == target_key and s.in_stock for s in stores):
            checks += 1
        if _ == 0:
            time.sleep(3)

    return checks >= 2


def confirm_delivery(
    offer: ActionableOffer,
    retailers: list[Retailer],
    *,
    use_browser: bool,
) -> bool:
    """Re-verifie le revendeur en ligne avant alerte livraison."""
    subset = [r for r in retailers if r.id == offer.retailer_id]
    if not subset:
        return False

    results = check_all_retailers(subset, use_browser=use_browser)
    if not results:
        return False

    if not delivery_available_online(results[0]):
        return False

    time.sleep(3)
    results2 = check_all_retailers(subset, use_browser=use_browser)
    if not results2:
        return False

    return delivery_available_online(results2[0])


def confirm_actionable_offer(
    offer: ActionableOffer,
    *,
    postal_code: str,
    radius_km: float,
    retailers: list[Retailer],
    use_browser: bool,
) -> bool:
    if not _confirm_enabled():
        return True

    if offer.kind == "magasin":
        return confirm_local_store(offer, postal_code, radius_km)
    if offer.kind == "livraison":
        return confirm_delivery(offer, retailers, use_browser=use_browser)
    return False
