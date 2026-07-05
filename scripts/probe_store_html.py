import json
import re
import requests

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15",
    "Accept-Language": "fr-FR,fr;q=0.9",
})

PRODUCT = "https://www.boulanger.com/ref/1216685"
CASTO = "https://www.castorama.fr/climatiseur-split-midea-reversible-3500w/8431312260509_CAFR.prd"

r = session.get(PRODUCT, timeout=25)
for pat in [
    r"disponib[^<]{0,80}magasin[^<]{0,80}",
    r'"storeName"\s*:\s*"[^"]+"',
    r'"siteLabel"\s*:\s*"[^"]+"',
]:
    hits = re.findall(pat, r.text, re.I)
    if hits:
        print("BO", hits[:3])

for store_id, name in [("1489", "merignac"), ("1059", "begles")]:
    s = requests.Session()
    s.headers.update(session.headers)
    s.cookies.set("storeId", store_id, domain=".castorama.fr")
    s.cookies.set("favouriteStore", store_id, domain=".castorama.fr")
    h = s.get(CASTO, timeout=25).text
    print(f"\nCASTO {store_id} len {len(h)}")
    for pat in [
        r'"availabilityStatus"\s*:\s*"[^"]+"',
        r'"inStock"\s*:\s*(true|false)',
        r'"clickAndCollect"\s*:\s*\{[^}]{0,300}',
    ]:
        hits = re.findall(pat, h, re.I)
        if hits:
            print(" ", hits[0][:250])

# Boulanger product JS - search sites/search usage
js = requests.get(
    "https://www.boulanger.com/etc.clientlibs/boulanger-site/clientlibs/wpk.app/blg.product.b1c250982d62c42975a5.js",
    timeout=25,
).text
idx = js.find("sites/search")
while idx >= 0 and idx < len(js):
    print("\nJS sites/search ctx:", js[max(0, idx - 150) : idx + 200])
    idx = js.find("sites/search", idx + 1)
    if idx > 0 and js.find("sites/search", idx) == idx:
        break
    if js.count("sites/search") > 3:
        break

for term in ["local-stock/search", "localStock/search", "siteSearch", "zipCode", "siteCode"]:
    if term in js:
        i = js.find(term)
        print(f"\n{term}:", js[max(0, i - 100) : i + 150])
