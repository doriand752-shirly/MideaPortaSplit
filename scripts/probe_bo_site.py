import json
import re
import requests

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15"})

h = session.get("https://www.boulanger.com/ref/1216685", timeout=25).text
d = json.loads(re.search(r"var G_CONFIG = (\{[\s\S]*?\});", h).group(1))

hdr = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Origin": "https://www.boulanger.com",
    "Referer": "https://www.boulanger.com/ref/1216685",
    "x-api-key": d["clientSiteApiKey"],
}

site_base = "https://www.boulanger.com/api/referential/site-v4"
filters = [
    {"filter": {"zipCode": "33700", "distance": 50000}},
    {"filter": {"zipCode": "33700", "distanceInKm": 50}},
    {"filter": {"coordinates": {"lat": 44.8323, "lng": -0.6817}, "distance": 50000}},
    {"filter": {"cityCode": "33281"}},
    {"filter": {"countryCode": "FRA", "zipCode": "33700"}},
    {"filter": {"location": {"zipCode": "33700", "countryCode": "FRA"}}},
    {"filter": {"address": {"zipCode": "33700", "countryCode": "FRA"}}},
    {"filter": {"postalCode": "33700"}},
    {"filter": {"zipCode": "33700", "countryCodeIso3": "FRA", "radius": 30}},
]
for body in filters:
    r = session.post(site_base + "/sites/search", headers=hdr, json=body, timeout=15)
    print(body, "->", r.status_code, r.text[:500])
    print("---")

# HTML embedded data
for pat in [r"storeInfos[^}]{0,500}", r'"siteCode"\s*:\s*"[^"]+"', r"MERIGNAC"]:
    hits = re.findall(pat, h, re.I)
    if hits:
        print("HTML", pat, hits[0][:400])

# promise keys
for key_name in ["clientPromiseApiKey", "clientBffApiKey"]:
    ph = {**hdr, "x-api-key": d[key_name]}
    r = session.post(
        "https://www.boulanger.com/api/commerce/promise-v2/local-stock/search",
        headers=ph,
        json={"filter": {"skuId": "1216685", "zipCode": "33700", "cityCode": "33281"}},
        timeout=15,
    )
    print(f"promise key={key_name}", r.status_code, r.text[:300])
