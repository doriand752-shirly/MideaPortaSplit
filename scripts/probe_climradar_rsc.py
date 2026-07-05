import re
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Accept": "text/x-component",
    "RSC": "1",
}

def fetch(path, rsc=False):
    h = {**HEADERS, "Next-Url": path}
    if not rsc:
        h["Accept"] = "text/html"
        del h["RSC"]
    r = requests.get(f"https://climradar.fr{path}", headers=h, timeout=30)
    return r.text

for path in ["/produit/portasplit", "/stock/portasplit?cp=33400"]:
    for rsc in [False, True]:
        t = fetch(path, rsc=rsc)
        label = ("RSC" if rsc else "HTML") + " " + path
        print(f"\n=== {label} len={len(t)} ===")
        keywords = [
            "leroy-merlin", "leroy_merlin", "Leroy Merlin",
            "retailerId", "lastSeenMinAgo", "en_stock", "rupture",
            "onlineOffers", "storeOffers", "retailers",
            "lowPrice", "highPrice", "AggregateOffer",
            "Darty", "Boulanger", "Castorama", "ManoMano",
            "33400", "Merignac", "merignac",
        ]
        for kw in keywords:
            c = t.count(kw)
            if c:
                print(f"  {kw}: {c}")

        # dump context around interesting tokens
        for kw in ["retailerId", "onlineOffers", "storeEntries", "lastSeenMinAgo"]:
            idx = t.find(kw)
            if idx >= 0:
                print(f"  ctx {kw}:", repr(t[idx:idx+300])[:350])

        # find all price-like patterns near retailer names
        for m in re.finditer(r'(leroy-merlin|castorama|boulanger|darty|amazon|manomano|fnac)[^\\]{0,200}', t, re.I):
            snippet = m.group(0)[:180]
            if "price" in snippet.lower() or "stock" in snippet.lower() or "status" in snippet.lower():
                print("  retailer snippet:", snippet[:180])
