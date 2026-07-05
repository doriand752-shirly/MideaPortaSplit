import json
import re
import requests

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
    "Accept-Language": "fr-FR,fr;q=0.9",
})

h = session.get("https://www.boulanger.com/ref/1216685", timeout=25).text
d = json.loads(re.search(r"var G_CONFIG = (\{[\s\S]*?\});", h).group(1))

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Origin": "https://www.boulanger.com",
    "Referer": "https://www.boulanger.com/ref/1216685",
    "x-api-key": d["clientBffApiKey"],
}

base = "https://www.boulanger.com/api/exchange/web/bcomtec/bff-frontomc-v1"

bodies = [
    {"skuId": "1216685", "postalCode": "33700", "countryCode": "FRA"},
    {"productId": 1216685, "postalCode": "33700"},
    {"items": [{"skuId": "1216685", "quantity": 1}], "postalCode": "33700", "shippingMethods": ["STORE"]},
    {"skuId": "1216685", "postalCode": "33700", "shippingMethodCode": "STORE"},
]

paths = [
    "/delivery/availability",
    "/shipping/availability",
    "/products/availability",
    "/store/availability",
    "/local-stock",
    "/promise",
    "/delivery/promise",
]

for path in paths:
    for body in bodies[:2]:
        r = session.post(base + path, headers=headers, json=body, timeout=15)
        if r.status_code != 404:
            print("POST", path, r.status_code, r.text[:350])
    r = session.get(base + path + "?skuId=1216685&postalCode=33700", headers=headers, timeout=15)
    if r.status_code != 404:
        print("GET", path, r.status_code, r.text[:350])

# estimation API with estimation key
est_headers = {**headers, "x-api-key": d["clientEstimationApiKey"]}
est_base = "https://www.boulanger.com/api/commerce/estimation-v1"
for path in ["/promise", "/delivery", "/shipping-methods", "/availability"]:
    for body in bodies[:3]:
        r = session.post(est_base + path, headers=est_headers, json=body, timeout=15)
        if r.status_code not in (404, 405):
            print("EST POST", path, body.keys(), r.status_code, r.text[:350])
