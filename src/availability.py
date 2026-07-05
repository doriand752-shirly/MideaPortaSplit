"""Determine si une offre est actionnable depuis un code postal (magasin OU livraison)."""

from __future__ import annotations

from dataclasses import dataclass

from .local_stores import LocalStoreStock
from .models import StockResult, StockStatus

# En stock en ligne = livraison France metropolitaine vers le code postal
DELIVERY_ONLINE_RETAILERS = frozenset(
    {
        "boulanger",
        "castorama",
        "optimea",
        "amazon",
        "fnac",
        "manomano",
        "darty",
    }
)

# Enseignes avec magasins suivis localement (retrait prioritaire)
LOCAL_PICKUP_RETAILERS = frozenset(
    {
        "leroy_merlin",
        "castorama",
        "boulanger",
        "darty",
    }
)


@dataclass
class ActionableOffer:
    kind: str  # "livraison" | "magasin"
    retailer_id: str
    retailer_name: str
    detail: str
    price: str | None
    url: str
    state_key: str
    store: LocalStoreStock | None = None
    stock_result: StockResult | None = None


def delivery_available_online(result: StockResult) -> bool:
    if result.status != StockStatus.IN_STOCK:
        return False
    if result.retailer.id not in DELIVERY_ONLINE_RETAILERS:
        return False
    # Leroy Merlin via ClimRadar seul : le stock national est souvent regional (magasin).
    # On ne declenche la livraison LM que via les checks directs, pas ClimRadar national.
    if result.retailer.id == "leroy_merlin":
        return False
    return True


def pickup_available_local(
    retailer_id: str,
    local_stores: list[LocalStoreStock],
) -> list[LocalStoreStock]:
    return [
        s
        for s in local_stores
        if s.retailer_id == retailer_id and s.in_stock
    ]


def build_actionable_offers(
    online_results: list[StockResult],
    local_stores: list[LocalStoreStock],
    postal_code: str,
) -> list[ActionableOffer]:
    offers: list[ActionableOffer] = []

    for store in local_stores:
        if not store.in_stock:
            continue
        offers.append(
            ActionableOffer(
                kind="magasin",
                retailer_id=store.retailer_id,
                retailer_name=store.store_name,
                detail=f"Retrait magasin — {store.distance_km} km de {postal_code}",
                price=None,
                url=store.product_url,
                state_key=store.state_key,
                store=store,
            )
        )

    retailers_with_local_pickup = {o.retailer_id for o in offers if o.kind == "magasin"}

    for result in online_results:
        if not delivery_available_online(result):
            continue
        offers.append(
            ActionableOffer(
                kind="livraison",
                retailer_id=result.retailer.id,
                retailer_name=result.retailer.name,
                detail=f"Livraison vers {postal_code} — {result.detail}",
                price=result.price,
                url=result.retailer.url,
                state_key=f"livraison:{result.retailer.id}",
                stock_result=result,
            )
        )

    return offers


def format_actionable_summary(
    offers: list[ActionableOffer],
    online_results: list[StockResult],
    local_stores: list[LocalStoreStock],
    postal_code: str,
    radius_km: float,
) -> str:
    lines = [
        f"Disponibilite actionnable pour {postal_code}",
        "(magasin < {0:.0f} km OU livraison)".format(radius_km),
        "",
    ]

    delivery = [o for o in offers if o.kind == "livraison"]
    pickup = [o for o in offers if o.kind == "magasin"]

    if delivery:
        lines.append("LIVRAISON :")
        for o in delivery:
            price = f" ({o.price})" if o.price else ""
            lines.append(f"  [OK] {o.retailer_name}{price}")
            lines.append(f"       -> {o.detail}")
    else:
        lines.append("LIVRAISON : aucune pour l'instant")

    lines.append("")
    if pickup:
        lines.append("MAGASIN :")
        for o in pickup:
            lines.append(f"  [OK] {o.retailer_name}")
            lines.append(f"       -> {o.detail}")
    else:
        lines.append(f"MAGASIN (< {radius_km:.0f} km) : aucun stock")

    lines.append("")
    lines.append("--- Detail en ligne ---")
    for result in online_results:
        icon = "[OK]" if result.status == StockStatus.IN_STOCK else "[--]"
        livraison = (
            "livraison OK"
            if delivery_available_online(result)
            else "pas de livraison detectee"
        )
        price = f" ({result.price})" if result.price else ""
        lines.append(f"{icon} {result.retailer.name}{price} — {livraison}")

    if local_stores:
        lines.append("")
        lines.append(f"--- Magasins suivis ({len(local_stores)}) ---")
        for store in local_stores:
            icon = "[OK]" if store.in_stock else "[--]"
            lines.append(f"{icon} {store.store_name} ({store.distance_km} km)")

    if not offers:
        lines.append("")
        lines.append("Rien d'actionnable pour l'instant.")

    return "\n".join(lines)
