"""Probe Leroy Merlin store stock for Merignac."""
import json
import re

import requests
from playwright.sync_api import sync_playwright

PRODUCT_URL = (
    "https://www.leroymerlin.fr/produits/"
    "climatiseur-split-mobile-reversible-portasplit-midea-par-optimea-93857579.html"
)
PRODUCT_ID = "93857579"
STORES = {
    "merignac": "https://www.leroymerlin.fr/magasins/merignac-bordeaux.html",
    "gradignan": "https://www.leroymerlin.fr/magasins/gradignan-bordeaux.html",
    "bordeaux": "https://www.leroymerlin.fr/magasins/bordeaux.html",
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0",
    "Accept": "application/json",
    "Accept-Language": "fr-FR,fr;q=0.9",
}

# Try API endpoints
for path in [
    f"https://www.leroymerlin.fr/v3/products/{PRODUCT_ID}",
    f"https://www.leroymerlin.fr/v3/products/{PRODUCT_ID}/stores",
    "https://www.leroymerlin.fr/v3/stores?postalCode=33700",
]:
    try:
        r = requests.get(path, headers=headers, timeout=15)
        print(path.split("leroymerlin.fr")[-1], r.status_code, r.text[:300])
    except Exception as e:
        print("err", e)

print("\n--- Playwright with store cookie ---")
with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=["--disable-blink-features=AutomationControlled"],
    )
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36",
        locale="fr-FR",
        viewport={"width": 1366, "height": 768},
    )
    page = context.new_page()

    # Visit homepage first
    page.goto("https://www.leroymerlin.fr/", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3000)

    # Try set store via URL param
    page.goto(
        PRODUCT_URL + "?store=merignac-bordeaux",
        wait_until="domcontentloaded",
        timeout=60000,
    )
    page.wait_for_timeout(5000)
    html = page.content()
    print("product page len", len(html), "captcha" in html.lower())
    text = html.lower()
    for term in ["merignac", "en stock", "disponible", "rupture", "ajouter", "93857579"]:
        print(term, text.count(term))

    # Capture API responses
    responses = []

    def on_response(response):
        if "leroymerlin" in response.url and (
            "product" in response.url or "store" in response.url or "stock" in response.url
        ):
            try:
                if response.status == 200 and "json" in response.headers.get("content-type", ""):
                    responses.append((response.url, response.json()))
            except Exception:
                pass

    page.on("response", on_response)
    page.reload(wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(3000)
    print("json responses", len(responses))
    for url, data in responses[:5]:
        print(" ", url[:80])
        print(" ", str(data)[:200])

    browser.close()
