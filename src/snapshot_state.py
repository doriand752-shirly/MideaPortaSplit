"""Persistance alertes / stock via snapshot.json (GitHub Actions)."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .models import StockStatus
from .snapshot_export import (
    SNAPSHOT_ALERT_DATES_FIELD,
    SNAPSHOT_HEARTBEAT_FIELD,
    SNAPSHOT_STOCK_STATE_FIELD,
)
from .heartbeat import HEARTBEAT_STATE_KEY
from .state import StateStore


def today_local() -> str:
    tz_name = os.getenv("HEARTBEAT_TIMEZONE", "Europe/Paris").strip() or "Europe/Paris"
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("Europe/Paris")
    return datetime.now(tz).date().isoformat()


def seed_store_from_snapshot(store: StateStore, snapshot_path: Path) -> None:
    """Rehydrate etat alertes depuis le snapshot commité (cache Actions peu fiable)."""
    if not snapshot_path.exists():
        return
    try:
        data = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return

    last_hb = data.get(SNAPSHOT_HEARTBEAT_FIELD)
    if isinstance(last_hb, str) and last_hb and not store.get_meta(HEARTBEAT_STATE_KEY):
        store.set_meta(HEARTBEAT_STATE_KEY, last_hb)

    stock_state = data.get(SNAPSHOT_STOCK_STATE_FIELD)
    if isinstance(stock_state, dict):
        for key, status in stock_state.items():
            if not isinstance(key, str) or not isinstance(status, str):
                continue
            entry = store._data.get(key)
            if isinstance(entry, dict) and entry.get("status"):
                continue
            store._data[key] = {
                "status": status,
                "detail": entry.get("detail", "") if isinstance(entry, dict) else "",
                "url": entry.get("url", "") if isinstance(entry, dict) else "",
            }

    alert_dates = data.get(SNAPSHOT_ALERT_DATES_FIELD)
    if isinstance(alert_dates, dict):
        for key, day in alert_dates.items():
            if isinstance(key, str) and isinstance(day, str) and day:
                if not store.get_alert_date(key):
                    store.set_alert_date(key, day)


def should_send_stock_alert(store: StateStore, state_key: str, today: str | None = None) -> bool:
    """True si une notification stock peut partir (max 1 / magasin / jour)."""
    day = today or today_local()
    if store.get_alert_date(state_key) == day:
        return False
    if store.get_last_status(state_key) == StockStatus.IN_STOCK.value:
        return False
    return True


def record_stock_alert(store: StateStore, state_key: str, today: str | None = None) -> None:
    store.set_alert_date(state_key, today or today_local())
