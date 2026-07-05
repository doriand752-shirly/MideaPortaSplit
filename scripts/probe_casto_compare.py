import json
import re
import requests

headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15",
    "Accept-Language": "fr-FR,fr;q=0.9",
}
EAN = "8431312260509"
PATH = f"climatiseur-split-midea-reversible-3500w/{EAN}_CAFR.prd"

def extract_signals(html, label):
    print(f"\n=== {label} ===")
    for pat in [
        r'"availabilityStatus"\s*:\s*"([^"]+)"',
        r'"inStock"\s*:\s*(true|false)',
        r'"stockStatus"\s*:\s*"([^"]+)"',
    ]:
        hits = re.findall(pat, html, re.I)
        if hits:
            print(pat[:35], hits[:5])
    for term in ["OUT_OF_STOCK", "IN_STOCK", "AVAILABLE", "UNAVAILABLE"]:
        print(term, html.count(term))

for store_id in ["1489", "1059"]:
    url = f"https://www.castorama.fr/store/{store_id}/{PATH}"
    h = requests.get(url, headers=headers, timeout=25).text
    extract_signals(h, f"store/{store_id}")
