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

    def get_last_status(self, retailer_id: str) -> str | None:
        entry = self._data.get(retailer_id)
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
