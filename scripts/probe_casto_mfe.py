import re
import requests

headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15"}
h = requests.get(
    "https://www.castorama.fr/store/1489/climatiseur-split-midea-reversible-3500w/8431312260509_CAFR.prd",
    headers=headers,
    timeout=25,
).text

for m in re.finditer(r"/_static/casto-browse-mfe/[^\"']+\.js", h):
    print(m.group(0)[:100])

m = re.search(r"fulfilment-options-[A-Za-z0-9_-]+\.js", h)
print("fulfilment chunk", m.group(0) if m else None)
