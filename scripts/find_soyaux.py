import re
import requests

HEADERS = {"User-Agent": "Mozilla/5.0"}
HUBS = [
    "bordeaux", "la-rochelle", "limoges", "pau", "bayonne", "nantes",
    "toulouse", "montpellier", "perigueux", "agen", "libourne", "niort",
    "poitiers", "cognac", "soyaux", "angouleme", "royan", "brive",
]

for hub in HUBS:
    r = requests.get(f"https://climradar.fr/stock/portasplit/{hub}", headers=HEADERS, timeout=10)
    if r.status_code != 200 or len(r.text) < 10000:
        continue
    text = r.text.lower()
    if any(t in text for t in ("soyaux", "cognac", "angoul")):
        print(f"=== {hub} ===")
        for m in re.finditer(r".{0,60}(soyaux|cognac|angoul.{0,20}).{0,60}", r.text, re.I):
            clean = re.sub(r"<[^>]+>", " ", m.group())
            print(" ", " ".join(clean.split())[:120])

# product JSON
h = requests.get("https://climradar.fr/produit/portasplit", headers=HEADERS, timeout=15).text
for term in ("soyaux", "cognac", "angoul", "16800", "16100"):
    print("product", term, term.lower() in h.lower())
