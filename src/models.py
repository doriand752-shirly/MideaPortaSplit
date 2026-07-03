from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class StockStatus(str, Enum):
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"
    UNKNOWN = "unknown"
    ERROR = "error"


@dataclass
class Retailer:
    id: str
    name: str
    url: str
    expected_price: float | None = None
    max_price: float | None = None
    enabled: bool = True
    checker: str = "generic"


@dataclass
class StockResult:
    retailer: Retailer
    status: StockStatus
    detail: str = ""
    price: str | None = None

    @property
    def is_available(self) -> bool:
        return self.status == StockStatus.IN_STOCK
