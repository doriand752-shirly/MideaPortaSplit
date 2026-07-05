"""Message quotidien de vie (heartbeat) a heure fixe."""

from __future__ import annotations

import os
from datetime import datetime
from zoneinfo import ZoneInfo

from .notifiers import send_heartbeat_message
from .state import StateStore

HEARTBEAT_STATE_KEY = "heartbeat:last_date"


def heartbeat_config() -> tuple[bool, int, str]:
    enabled = os.getenv("HEARTBEAT_ENABLED", "true").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )
    try:
        hour = int(os.getenv("HEARTBEAT_HOUR", "18"))
    except ValueError:
        hour = 18
    hour = max(0, min(23, hour))
    tz = os.getenv("HEARTBEAT_TIMEZONE", "Europe/Paris").strip() or "Europe/Paris"
    return enabled, hour, tz


def should_send_heartbeat(store: StateStore) -> bool:
    enabled, target_hour, tz_name = heartbeat_config()
    if not enabled:
        return False

    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("Europe/Paris")

    now = datetime.now(tz)
    if now.hour < target_hour:
        return False

    today = now.date().isoformat()
    last = store.get_meta(HEARTBEAT_STATE_KEY)
    return last != today


def send_daily_heartbeat(
    store: StateStore,
    *,
    postal_code: str | None = None,
    actionable_count: int = 0,
    checks_count: int | None = None,
    force: bool = False,
) -> list[str]:
    if not force and not should_send_heartbeat(store):
        return []

    enabled, target_hour, tz_name = heartbeat_config()
    if not enabled and not force:
        return []

    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("Europe/Paris")

    now = datetime.now(tz)
    today = now.date().isoformat()

    channels = send_heartbeat_message(
        postal_code=postal_code or os.getenv("POSTAL_CODE", "?"),
        actionable_count=actionable_count,
        sent_at=now.strftime("%d/%m/%Y %H:%M"),
        target_hour=target_hour,
    )

    if channels:
        store.set_meta(HEARTBEAT_STATE_KEY, today)
        store.save()

    return channels
