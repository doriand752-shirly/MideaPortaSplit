from __future__ import annotations

import os
import time

import requests

from .availability import ActionableOffer
from .local_stores import LocalStoreStock
from .models import StockResult, StockStatus


def _format_delivery_message(result: StockResult, postal_code: str) -> str:
    lines = [
        "MIDEA PORTASPLIT — LIVRAISON DISPONIBLE",
        "",
        result.retailer.name,
    ]
    if result.price:
        lines.append(f"Prix : {result.price}")
    if result.retailer.expected_price:
        lines.append(f"Prix attendu : ~{int(result.retailer.expected_price)} EUR")
    lines.append(f"Livraison vers : {postal_code}")
    lines.extend(
        [
            f"Info : {result.detail}",
            "",
            f"Lien : {result.retailer.url}",
            "",
            "Commandez vite — les stocks partent en quelques heures.",
        ]
    )
    return "\n".join(lines)


def format_local_store_message(store: LocalStoreStock, postal_code: str) -> str:
    return "\n".join(
        [
            "MIDEA PORTASPLIT — RETRAIT MAGASIN",
            "",
            f"Magasin : {store.store_name}",
            f"Adresse : {store.location}",
            f"Distance : {store.distance_km} km depuis {postal_code}",
            "",
            f"Prix : {int(store.price)} EUR" if store.price else "",
            f"Lien : {store.product_url}",
            "",
            "Verifiez le retrait sur le site avant de vous deplacer.",
        ]
    )


def _retry_count() -> int:
    try:
        return max(1, int(os.getenv("NOTIFY_RETRIES", "3")))
    except ValueError:
        return 3


def send_telegram_text(bot_token: str, chat_id: str, text: str) -> None:
    response = requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": False,
        },
        timeout=20,
    )
    response.raise_for_status()


def _post_with_retry(
    label: str,
    send_fn,
) -> bool:
    retries = _retry_count()
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            send_fn()
            return True
        except requests.RequestException as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(min(2 ** attempt, 10))
    if last_error:
        print(f"[ERREUR] {label} apres {retries} essais : {last_error}", flush=True)
    return False


def _dispatch_message(
    message: str,
    *,
    ntfy_title: str,
    ntfy_priority: str = "urgent",
) -> list[str]:
    sent: list[str] = []

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if bot_token and chat_id:
        if _post_with_retry(
            "Telegram",
            lambda: send_telegram_text(bot_token, chat_id, message),
        ):
            sent.append("telegram")

    webhook = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    if webhook:
        if _post_with_retry(
            "Discord",
            lambda: requests.post(
                webhook, json={"content": message}, timeout=20
            ).raise_for_status(),
        ):
            sent.append("discord")

    ntfy_topic = os.getenv("NTFY_TOPIC", "").strip()
    if ntfy_topic:
        if _post_with_retry(
            "ntfy",
            lambda: requests.post(
                f"https://ntfy.sh/{ntfy_topic}",
                data=message.encode("utf-8"),
                headers={"Title": ntfy_title, "Priority": ntfy_priority},
                timeout=20,
            ).raise_for_status(),
        ):
            sent.append("ntfy")

    return sent


def notify_actionable_offer(offer: ActionableOffer, postal_code: str) -> list[str]:
    if offer.kind == "magasin" and offer.store:
        message = format_local_store_message(offer.store, postal_code)
        title = "PortaSplit — magasin proche"
    elif offer.stock_result:
        message = _format_delivery_message(offer.stock_result, postal_code)
        title = "PortaSplit — livraison"
    else:
        return []

    return _dispatch_message(message, ntfy_title=title)


def notify_stock_available(result: StockResult) -> list[str]:
    postal_code = os.getenv("POSTAL_CODE", "").strip() or "?"
    message = _format_delivery_message(result, postal_code)
    return _dispatch_message(message, ntfy_title="Midea PortaSplit EN STOCK")


def test_telegram() -> tuple[bool, str]:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    if not bot_token:
        return False, "TELEGRAM_BOT_TOKEN manquant dans .env"
    if not chat_id:
        return False, "TELEGRAM_CHAT_ID manquant dans .env"

    try:
        send_telegram_text(
            bot_token,
            chat_id,
            "Test MideaPortaSplit OK\n\n"
            "Alertes : magasin < 100 km du 33000 OU livraison vers votre code postal.",
        )
    except requests.HTTPError as exc:
        body = exc.response.text[:300] if exc.response is not None else ""
        return False, f"Erreur Telegram: {exc} {body}"
    except requests.RequestException as exc:
        return False, f"Erreur reseau: {exc}"

    return True, "Message de test envoye — verifiez Telegram."


def send_heartbeat_message(
    *,
    postal_code: str,
    actionable_count: int,
    sent_at: str,
    target_hour: int,
) -> list[str]:
    if actionable_count:
        stock_line = f"Stock actionnable : {actionable_count} offre(s)"
    else:
        stock_line = "Stock actionnable : aucun pour l'instant"

    radius = os.getenv("LOCAL_RADIUS_KM", "100")
    interval = os.getenv("CHECK_INTERVAL_MINUTES", "2")

    message = "\n".join(
        [
            "Midea PortaSplit — surveillance active",
            "",
            "Le moniteur tourne toujours.",
            f"Zone : {postal_code} (magasins < {radius} km + livraison)",
            f"Verification toutes les {interval} min",
            stock_line,
            f"Rapport du {sent_at}",
            "",
            f"Prochain rapport quotidien vers {target_hour}h.",
        ]
    )
    return _dispatch_message(
        message,
        ntfy_title="PortaSplit — OK",
        ntfy_priority="low",
    )


def format_summary(results: list[StockResult]) -> str:
    lines = ["Detail en ligne", ""]
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
