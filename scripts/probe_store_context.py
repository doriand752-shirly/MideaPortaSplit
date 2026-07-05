import json
import re
import requests

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
    "Accept-Language": "fr-FR,fr;q=0.9",
})

# Boulanger - session cookies + promise
r = session.get("https://www.boulanger.com/ref/1216685", timeout=25)
d = json.loads(re.search(r"var G_CONFIG = (\{[\s\S]*?\});", r.text).group(1))
print("cookies", list(session.cookies.keys())[:10])

for key in ["clientPromiseApiKey", "clientEstimationApiKey"]:
    resp = session.post(
        "https://www.boulanger.com/api/commerce/promise-v2/local-stock/search",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": "https://www.boulanger.com",
            "Referer": "https://www.boulanger.com/ref/1216685",
            "x-api-key": d[key],
        },
        json={"filter": {"skuId": "1216685", "zipCode": "33700", "cityCode": "33281"}},
        timeout=15,
    )
    print("promise+cookie", key, resp.status_code, resp.text[:400])

# Search product HTML for site codes
for m in re.finditer(r'"siteCode"\s*:\s*"(\d+)"', r.text):
    print("siteCode", m.group(1))

# Castorama fulfilment API from page scripts
casto = session.get(
    "https://www.castorama.fr/climatiseur-split-midea-reversible-3500w/8431312260509_CAFR.prd",
    timeout=25,
).text
for pat in [
    r"https://[^\"']+fulfil[^\"']+",
    r"https://[^\"']+stock[^\"']+api[^\"']+",
    r"/gateway/[^\"']+",
    r"storeId[\"']?\s*:\s*[\"']?(\d+)",
]:
    hits = sorted(set(re.findall(pat, casto, re.I)))
    if hits:
        print("\nCASTO", pat[:30], hits[:8])

# LM store context URLs
LM = "https://www.leroymerlin.fr/produits/climatiseur-split-mobile-reversible-portasplit-midea-par-optimea-93857579.html"
for suffix in [
    "",
    "?store=merignac",
    "?magasin=merignac",
    "?storeId=63",
]:
    lr = session.get(LM + suffix, timeout=25)
    print("\nLM", suffix or "(base)", lr.status_code, len(lr.text))
    low = lr.text.lower()
    if "merignac" in low:
        idx = low.find("merignac")
        print("  merignac ctx:", re.sub(r"\s+", " ", lr.text[idx - 80 : idx + 120])[:200])
    for term in ["en stock", "rupture", "disponible en magasin", "retrait"]:
        if term in low:
            print(f"  {term}: {low.count(term)}")

# Darty store
DARTY = "https://www.darty.com/nav/achat/petit_electromenager/traitement_air/climatiseur/midea_mmcs-12hrn8-qrd0.html"
dr = session.get(DARTY, timeout=25)
print("\nDARTY", dr.status_code, len(dr.text))
for term in ["33700", "merignac", "retrait", "magasin"]:
    if term in dr.text.lower():
        print(f"  {term} found")
