import json
import re
import requests

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15"})
h = session.get("https://www.boulanger.com/ref/1216685", timeout=25).text
d = json.loads(re.search(r"var G_CONFIG = (\{[\s\S]*?\});", h).group(1))

def hdr(key_name):
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Origin": "https://www.boulanger.com",
        "Referer": "https://www.boulanger.com/ref/1216685",
        "x-api-key": d[key_name],
    }

geo = "https://www.boulanger.com/api/referential/geography-v3"
for path, body in [
    ("/shops/search", {"filter": {"zipCode": "33700"}}),
    ("/shops/search", {"filter": {"cityCode": "33281"}}),
    ("/shops/search", {"filter": {"zipCode": "33700", "radius": 30}}),
    ("/points-of-sale/search", {"filter": {"zipCode": "33700"}}),
    ("/stores/search", {"filter": {"zipCode": "33700"}}),
    ("/shop/search", {"filter": {"zipCode": "33700"}}),
]:
    r = session.post(geo + path, headers=hdr("clientGeographyApiKey"), json=body, timeout=15)
    if r.status_code != 404:
        print(path, r.status_code, r.text[:600])
        print("---")

# estimation with store availability
est = "https://www.boulanger.com/api/commerce/estimation-v1"
for path, body in [
    ("/shipping-methods", {"filter": {"skuId": "1216685", "zipCode": "33700", "cityCode": "33281"}}),
    ("/shipping-methods", {"skuId": "1216685", "zipCode": "33700", "cityCode": "33281"}),
    ("/store-availability", {"filter": {"skuId": "1216685", "zipCode": "33700"}}),
    ("/availability", {"items": [{"skuId": "1216685"}], "zipCode": "33700", "cityCode": "33281"}),
]:
    r = session.post(est + path, headers=hdr("clientEstimationApiKey"), json=body, timeout=15)
    if r.status_code not in (404, 405):
        print("EST", path, r.status_code, r.text[:600])
        print("---")

# bff
bff = "https://www.boulanger.com/api/exchange/web/bcomtec/bff-frontomc-v1"
for path, body in [
    ("/shipping-methods", {"skuId": "1216685", "zipCode": "33700"}),
    ("/local-stock", {"skuId": "1216685", "zipCode": "33700"}),
    ("/products/1216685/shipping", {"zipCode": "33700", "cityCode": "33281"}),
]:
    r = session.post(bff + path, headers=hdr("clientBffApiKey"), json=body, timeout=15)
    if r.status_code not in (404, 405):
        print("BFF", path, r.status_code, r.text[:600])
