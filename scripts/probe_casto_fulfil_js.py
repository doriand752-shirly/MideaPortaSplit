import re
import requests

js = requests.get(
    "https://www.castorama.fr/_static/casto-browse-mfe/v0-677-1/get-fulfilment-options-CjZyTRWm.js",
    timeout=25,
).text
print("len", len(js))
urls = sorted(set(re.findall(r'https://[^"\']+|/gateway/[^"\']+|/api/[^"\']+', js)))
for u in urls:
    if any(k in u.lower() for k in ["api", "graphql", "fulfil", "stock", "product", "store", "casto"]):
        print(u[:160])

for term in ["fulfilmentOptions", "operationName", "graphql", "storeId", "ean"]:
    if term in js:
        i = js.find(term)
        print(f"\n{term}:", js[max(0, i - 60) : i + 120])
