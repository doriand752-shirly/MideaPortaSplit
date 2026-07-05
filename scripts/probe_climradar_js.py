import json
import re
import sys

import requests

BASE = "https://climradar.fr"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0"}
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

html = requests.get(f"{BASE}/produit/portasplit", headers=HEADERS, timeout=30).text
chunks = sorted(set(re.findall(r"/_next/static/chunks/[^\"']+\.js", html)))

patterns = [
    r"/api/[a-zA-Z0-9_/?=&.-]{5,80}",
    r'kind:\s*"[^"]+"',
    r"stockByStore",
    r"zone-preview",
]

for chunk in chunks:
    js = requests.get(BASE + chunk, headers=HEADERS, timeout=20).text
    if "/api/" not in js:
        continue
    hits = set(re.findall(r'["\'](/api/[^"\']+)["\']', js))
    if hits:
        print(chunk.split("/")[-1], sorted(hits))

# Find product page fetch for online offers
for chunk in chunks:
    js = requests.get(BASE + chunk, headers=HEADERS, timeout=20).text
    if "kind=product" in js or 'kind:"product"' in js or "live?kind" in js:
        print("\nLIVE in", chunk.split("/")[-1])
        for m in re.finditer(r".{0,60}(live|/api/).{0,100}", js):
            s = m.group(0)
            if "api" in s:
                print(" ", s[:160])

# Test product-specific endpoints from JS
for path in [
    "/api/live?kind=product&id=portasplit&country=FR",
    "/api/live?kind=online&id=portasplit",
    "/api/live?kind=retailer&id=portasplit",
    "/api/products/portasplit",
    "/api/product/portasplit/offers",
]:
    r = requests.get(BASE + path, headers={**HEADERS, "Accept": "application/json"}, timeout=20)
    print(path, r.status_code, r.text[:200].replace("\n", " "))
