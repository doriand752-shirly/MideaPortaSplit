import re
import requests

headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15"}
js = requests.get(
    "https://www.castorama.fr/_static/casto-browse-mfe/v0-677-1/pdp-i_45N5mb.js",
    timeout=25,
).text
print("len", len(js))
for term in ["compositeOfferId", "offerId", "productId"]:
    if term in js:
        i = js.find(term)
        print(term, js[max(0, i - 80) : i + 120])

h = requests.get(
    "https://www.castorama.fr/store/1489/climatiseur-split-midea-reversible-3500w/8431312260509_CAFR.prd",
    headers=headers,
    timeout=25,
).text
for pat in [r'"id"\s*:\s*"(\d{10,})"', r"8431312260509_[A-Za-z0-9]+"]:
    hits = re.findall(pat, h)
    if hits:
        print("html", pat, hits[:8])
