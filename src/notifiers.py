from __future__ import annotations

import os

import requests

from .models import StockResult, StockStatus


def _format_message(result: StockResult) -> str:
    lines = [
        "🟢 MIDEA PORTASPLIT EN STOCK !",
        "",
        f"🏪 {result.retailer.name}",
    ]
    if result.price:
        lines.append(f"💰 Prix détecté : {result.price}")
    if result.retailer.expected_price:
        lines.append(f"📌 Prix attendu : ~{int(result.retailer.expected_price)} €")
    lines.extend(
        [
            f"ℹ️ {result.detail}",
            "",
            f"🔗 {result.retailer.url}",
            "",
            "⚡ Commandez vite — les stocks partent en quelques heures.",
        ]
    )
    return "\n".join(lines)


def send_telegram(result: StockResult, bot_token: str, chat_id: str) -> None:
    message = _format_message(result)
    response = requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": message,
            "disable_web_page_preview": False,
        },
        timeout=20,
    )
    response.raise_for_status()


def send_discord(result: StockResult, webhook_url: str) -> None:
    message = _format_message(result)
    response = requests.post(
        webhook_url,
        json={"content": message},
        timeout=20,
    )
    response.raise_for_status()


def send_ntfy(result: StockResult, topic: str) -> None:
    message = _format_message(result)
    response = requests.post(
        f"https://ntfy.sh/{topic}",
        data=message.encode("utf-8"),
        headers={
            "Title": "Midea PortaSplit EN STOCK",
            "Priority": "urgent",
            "Tags": "rotating_light,shopping_bags",
        },
        timeout=20,
    )
    response.raise_for_status()


def notify_stock_available(result: StockResult) -> list[str]:
    sent: list[str] = []

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if bot_token and chat_id:
        send_telegram(result, bot_token, chat_id)
        sent.append("telegram")

    webhook = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    if webhook:
        send_discord(result, webhook)
        sent.append("discord")

    ntfy_topic = os.getenv("NTFY_TOPIC", "").strip()
    if ntfy_topic:
        send_ntfy(result, ntfy_topic)
        sent.append("ntfy")

    return sent


def format_summary(results: list[StockResult]) -> str:
    lines = ["Resume surveillance Midea PortaSplit", ""]
    for result in results:
        icon = {
            StockStatus.IN_STOCK: "[OK]",
            StockStatus.OUT_OF_STOCK: "[--]",
            StockStatus.UNKNOWN: "[??]",
            StockStatus.ERROR: "[!!]",
        }[result.status]
        price = f" ({result.price})" if result.price else ""
        lines.append(f"{icon} {result.retailer.name}: {result.status.value}{price}")
        if result.detail:
            lines.append(f"    -> {result.detail}")
    return "\n".join(lines)
