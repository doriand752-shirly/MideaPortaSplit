from __future__ import annotations

import random
import re
import time
from urllib.parse import urlparse

import requests

DEFAULT_TIMEOUT = 12

SAFARI_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/17.4 Safari/605.1.15"
)

PROTECTED_RETAILER_IDS = frozenset({"darty", "leroy_merlin", "fnac", "manomano"})

HOMEPAGES: dict[str, str] = {
    "darty": "https://www.darty.com/",
    "leroy_merlin": "https://www.leroymerlin.fr/",
    "fnac": "https://www.fnac.com/",
    "manomano": "https://www.manomano.fr/",
}

BOT_BLOCK_PATTERNS = [
    re.compile(p, re.I)
    for p in (
        r"datadome",
        r"captcha-delivery",
        r"geo\.captcha",
        r"challenge-platform",
        r"please enable javascript",
        r"access.?denied",
        r"_Incapsula_Resource",
        r"cf-browser-verification",
        r"attention required",
        r"bot detection",
        r"hcaptcha",
        r"recaptcha",
    )
]


def is_bot_blocked(html: str) -> bool:
    if len(html) < 800:
        return True
    return any(p.search(html) for p in BOT_BLOCK_PATTERNS)


def _nav_headers(*, referer: str | None = None, same_origin: bool = False) -> dict[str, str]:
    headers = {
        "User-Agent": SAFARI_UA,
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,*/*;q=0.8"
        ),
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin" if same_origin else "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    }
    if referer:
        headers["Referer"] = referer
    return headers


def fetch_stealth_http(
    url: str,
    retailer_id: str,
    *,
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """Visite la home puis la page produit (session + délai) pour limiter la détection bot."""
    session = requests.Session()
    homepage = HOMEPAGES.get(retailer_id)

    if homepage:
        session.get(homepage, timeout=timeout, headers=_nav_headers())
        time.sleep(0.85 + random.random() * 0.65)

    headers = _nav_headers(referer=homepage, same_origin=bool(homepage))
    response = session.get(url, timeout=timeout, allow_redirects=True, headers=headers)
    response.raise_for_status()

    if is_bot_blocked(response.text):
        raise RuntimeError("Page anti-bot (captcha / DataDome)")

    return response.text


def fetch_plain_http(url: str, *, timeout: int = DEFAULT_TIMEOUT) -> str:
    parsed = urlparse(url)
    referer = f"{parsed.scheme}://{parsed.netloc}/"
    response = requests.get(
        url,
        timeout=timeout,
        allow_redirects=True,
        headers=_nav_headers(referer=referer, same_origin=True),
    )
    response.raise_for_status()
    if is_bot_blocked(response.text):
        raise RuntimeError("Page anti-bot (captcha / DataDome)")
    return response.text


def fetch_for_retailer(url: str, retailer_id: str, *, timeout: int = DEFAULT_TIMEOUT) -> str:
    if retailer_id in PROTECTED_RETAILER_IDS:
        return fetch_stealth_http(url, retailer_id, timeout=timeout)
    return fetch_plain_http(url, timeout=timeout)
