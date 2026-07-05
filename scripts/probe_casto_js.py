import re
import requests

h = requests.get(
    "https://www.castorama.fr/climatiseur-split-midea-reversible-3500w/8431312260509_CAFR.prd",
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=25,
).text

for pat in [r'kf\.api\.castorama\.fr[^"\']+', r'/gateway/[^"\']+', r'fulfilment[^"\']{0,100}', r'storeId[^"\']{0,80}']:
    hits = sorted(set(re.findall(pat, h, re.I)))
    print(pat, len(hits))
    for x in hits[:15]:
        print(" ", x[:120])

# download fulfilment mfe chunk and search for api url
m = re.search(r'fulfilment-options-[A-Za-z0-9_-]+\.js', h)
if m:
    js_path = "/_static/casto-browse-mfe/v0-677-1/" + m.group(0)
    js = requests.get("https://www.castorama.fr" + js_path, timeout=25).text
    print("\njs len", len(js))
    for pat in [r'https://[^"\']+', r'/api/[^"\']+']:
        urls = sorted(set(re.findall(pat, js)))
        for u in urls:
            if any(k in u.lower() for k in ("avail", "store", "stock", "fulfil", "product")):
                print("js url", u[:120])
