import re
import requests

headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15",
    "Accept-Language": "fr-FR,fr;q=0.9",
}

EAN = "8431312260509"
CASTO_PATH = f"climatiseur-split-midea-reversible-3500w/{EAN}_CAFR.prd"
BO = "https://www.boulanger.com/ref/1216685"
LM = "https://www.leroymerlin.fr/produits/climatiseur-split-mobile-reversible-portasplit-midea-par-optimea-93857579.html"

casto_urls = [
    f"https://www.castorama.fr/{CASTO_PATH}",
    f"https://www.castorama.fr/store/1489/product/{EAN}",
    f"https://www.castorama.fr/store/1489/{CASTO_PATH}",
    f"https://www.castorama.fr/magasin/merignac/{CASTO_PATH}",
]

for url in casto_urls:
    r = requests.get(url, headers=headers, timeout=25, allow_redirects=True)
    low = r.text.lower()
    print("\nCASTO", url.split(".fr")[-1][:70])
    print("  status", r.status_code, "len", len(r.text), "final", r.url.split(".fr")[-1][:50])
    for term in ["en stock", "rupture", "indisponible", "clickandcollect", "1489", "merignac"]:
        if term in low:
            print(f"  {term}: {low.count(term)}")

# Boulanger store variants
for suffix in ["", "?store=121", "?siteCode=121", "?favoriteStore=121"]:
    r = requests.get(BO + suffix.replace("?", "?" if "?" in suffix else ""), headers=headers, timeout=25)
    if not suffix:
        url = BO
    else:
        url = BO + suffix
    r = requests.get(url, headers=headers, timeout=25)
    low = r.text.lower()
    print("\nBO", suffix or "(base)", r.status_code, len(r.text))
    for term in ["33700", "merignac", "retrait", "disponible", "magasin"]:
        if term in low:
            print(f"  {term}: {low.count(term)}")

# LM with iPhone UA
for url in [LM, LM + "?store=merignac-bordeaux", "https://www.leroymerlin.fr/v3/products/93857579/offers?storeCode=063"]:
    r = requests.get(url, headers=headers, timeout=25)
    print("\nLM", url.split("leroymerlin.fr")[-1][:60], r.status_code, len(r.text))
    if r.status_code == 200 and len(r.text) < 5000:
        print(" ", r.text[:300])

# Darty
DARTY = "https://www.darty.com/nav/achat/petit_electromenager/traitement_air/climatiseur/midea_mmcs-12hrn8-qrd0.html"
r = requests.get(DARTY, headers=headers, timeout=25)
print("\nDARTY iPhone", r.status_code, len(r.text))
