import json
import re
import requests

h = requests.get("https://www.boulanger.com/ref/1216685", headers={"User-Agent": "Mozilla/5.0"}, timeout=25).text
d = json.loads(re.search(r"var G_CONFIG = (\{[\s\S]*?\});", h).group(1))

for term in ["localStock", "local-stock", "LocalStock", "storeAvailability"]:
    print(term, h.count(term))

# Search all keys in G_CONFIG containing local or stock
for k, v in d.items():
    if "local" in k.lower() or "stock" in k.lower():
        print(k, "=>", v)

# Try bff-frontomc for local stock
bff_key = d.get("clientBffApiKey")
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
    "Accept": "application/json",
    "x-api-key": bff_key,
    "Origin": "https://www.boulanger.com",
    "Referer": "https://www.boulanger.com/ref/1216685",
}
base = "https://www.boulanger.com/api/exchange/web/bcomtec/bff-frontomc-v1"
for path in [
    "/products/1216685/local-stock?postalCode=33700",
    "/local-stock/products/1216685?postalCode=33700",
    "/products/1216685/stores/availability?postalCode=33700",
    "/store-availability?skuId=1216685&postalCode=33700",
]:
    r = requests.get(base + path, headers=headers, timeout=15)
    print(path, r.status_code, r.text[:400])
