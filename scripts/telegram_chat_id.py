"""Liste les chats (groupes, canaux, prives) vus par le bot Telegram.

Usage :
  1. Ajoute le bot dans ton groupe.
  2. Ecris un message dans le groupe (ex: "hello", ou mentionne le bot).
  3. Lance : python scripts/telegram_chat_id.py
  4. Repere la ligne "groupe" et copie son id (negatif) dans TELEGRAM_CHAT_ID (.env).

Astuce : si rien n'apparait, desactive le mode "privacy" du bot via
@BotFather -> /setprivacy -> Disable, puis reecris dans le groupe.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent


def _load_token() -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if token:
        return token
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("TELEGRAM_BOT_TOKEN="):
                return line.split("=", 1)[1].strip()
    return ""


def main() -> int:
    token = _load_token()
    if not token:
        print("TELEGRAM_BOT_TOKEN introuvable (env ou .env).")
        return 1

    resp = requests.get(
        f"https://api.telegram.org/bot{token}/getUpdates",
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()

    if not data.get("ok"):
        print(f"Reponse Telegram inattendue : {data}")
        return 1

    seen: dict[int, str] = {}
    for update in data.get("result", []):
        for key in ("message", "channel_post", "my_chat_member", "edited_message"):
            obj = update.get(key)
            if not obj:
                continue
            chat = obj.get("chat", {})
            cid = chat.get("id")
            if cid is None or cid in seen:
                continue
            ctype = chat.get("type", "?")
            title = chat.get("title") or chat.get("username") or chat.get("first_name") or ""
            seen[cid] = f"[{ctype}] {title}".strip()

    if not seen:
        print("Aucun chat detecte.")
        print("-> Ajoute le bot au groupe, ecris un message dedans, puis relance.")
        print("-> Si toujours rien : @BotFather /setprivacy -> Disable, puis reecris.")
        return 0

    print("Chats vus par le bot :\n")
    for cid, label in seen.items():
        marker = "  <-- groupe/canal" if cid < 0 else ""
        print(f"  chat_id = {cid}   {label}{marker}")
    print("\nCopie l'id du groupe (negatif) dans TELEGRAM_CHAT_ID (.env).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
