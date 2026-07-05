from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .models import StockResult, StockStatus


class StateStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._data: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            self._data = json.loads(self.path.read_text(encoding="utf-8"))
        else:
            self._data = {}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def get_last_status(self, key: str) -> str | None:
        entry = self._data.get(key)
        return entry.get("status") if entry else None

    def update(self, result: StockResult) -> bool:
        """Retourne True si le produit vient de passer en stock (nouvelle alerte)."""
        previous = self.get_last_status(result.retailer.id)
        now = datetime.now(timezone.utc).isoformat()

        became_available = (
            result.status == StockStatus.IN_STOCK
            and previous != StockStatus.IN_STOCK.value
        )

        self._data[result.retailer.id] = {
            "status": result.status.value,
            "detail": result.detail,
            "price": result.price,
            "url": result.retailer.url,
            "checked_at": now,
        }
        return became_available

    def update_local_store(self, store_key: str, in_stock: bool, detail: str, url: str) -> bool:
        previous = self.get_last_status(store_key)
        now = datetime.now(timezone.utc).isoformat()
        status = StockStatus.IN_STOCK.value if in_stock else StockStatus.OUT_OF_STOCK.value
        became_available = in_stock and previous != StockStatus.IN_STOCK.value
        self._data[store_key] = {
            "status": status,
            "detail": detail,
            "url": url,
            "checked_at": now,
        }
        return became_available

    def mark_missing_offers(
        self,
        active_keys: set[str],
        prefixes: tuple[str, ...] = ("local:", "livraison:"),
    ) -> None:
        for key, entry in list(self._data.items()):
            if not any(key.startswith(p) for p in prefixes):
                continue
            if key in active_keys:
                continue
            if entry.get("status") == "in_stock":
                self.update_local_store(key, False, "plus disponible", entry.get("url", ""))

    def get_meta(self, key: str) -> str | None:
        entry = self._data.get(key)
        if isinstance(entry, dict):
            return entry.get("value")
        if isinstance(entry, str):
            return entry
        return None

    def set_meta(self, key: str, value: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._data[key] = {"value": value, "updated_at": now}
