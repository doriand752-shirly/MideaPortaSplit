import json
import re
import requests

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15"})

h = session.get("https://www.boulanger.com/ref/1216685", timeout=25).text
d = json.loads(re.search(r"var G_CONFIG = (\{[\s\S]*?\});", h).group(1))

def hdr(key):
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Origin": "https://www.boulanger.com",
        "Referer": "https://www.boulanger.com/ref/1216685",
        "x-api-key": d[key],
    }

# Site search near zip
site_base = "https://www.boulanger.com/api/referential/site-v4"
for path, body in [
    ("/sites/search", {"filter": {"zipCode": "33700", "radius": 50}}),
    ("/sites/search", {"filter": {"zipCode": "33700"}}),
    ("/sites/search", {"zipCode": "33700", "radiusKm": 50}),
    ("/sites", None),
]:
    if body:
        r = session.post(site_base + path, headers=hdr("clientSiteApiKey"), json=body, timeout=15)
    else:
        r = session.get(site_base + path, headers=hdr("clientSiteApiKey"), timeout=15)
    print("SITE", path, r.status_code, r.text[:600])
    print("---")

# Promise API - local stock / store pickup
promise_base = "https://www.boulanger.com/api/commerce/promise-v2"
bodies = [
    {"filter": {"skuId": "1216685", "zipCode": "33700", "cityCode": "33281"}},
    {"skuId": "1216685", "zipCode": "33700", "cityCode": "33281", "deliveryModes": ["REM", "DRV"]},
    {"items": [{"skuId": "1216685", "quantity": 1}], "zipCode": "33700", "cityCode": "33281"},
    {"productId": "1216685", "postalCode": "33700", "shippingMethods": ["STORE", "PICKUP"]},
]
for path in [
    "/promises/search",
    "/promise/search",
    "/delivery-modes/search",
    "/local-stock/search",
    "/stores/availability/search",
    "/availability/search",
    "/shipping/search",
]:
    for body in bodies[:2]:
        r = session.post(promise_base + path, headers=hdr("clientPromiseApiKey"), json=body, timeout=15)
        if r.status_code not in (404, 405):
            print("PROMISE", path, r.status_code, r.text[:700])
            print("---")

# Estimation shipping methods
est = "https://www.boulanger.com/api/commerce/estimation-v1"
for path in ["/shipping-methods/search", "/shipping-methods"]:
    for body in bodies[:3]:
        r = session.post(est + path, headers=hdr("clientEstimationApiKey"), json=body, timeout=15)
        if r.status_code not in (404, 405):
            print("EST", path, r.status_code, r.text[:700])
            print("---")

# Merch API
merch = "https://www.boulanger.com/api/offer/merch-v3"
for path in [
    "/products/1216685/local-stock",
    "/products/1216685/stores",
    "/local-stock/search",
]:
    r = session.get(merch + path, headers=hdr("clientMerchApiKey"), timeout=15)
    if r.status_code != 404:
        print("MERCH GET", path, r.status_code, r.text[:500])
