import json
import re
import requests

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15"})

h = session.get("https://www.boulanger.com/ref/1216685", timeout=25).text
d = json.loads(re.search(r"var G_CONFIG = (\{[\s\S]*?\});", h).group(1))

# All Endpoint keys
for k in sorted(d.keys()):
    if "endpoint" in k.lower() or "Endpoint" in k:
        print(k, "=>", d[k])

# Try site search with filter as array
site_hdr = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Origin": "https://www.boulanger.com",
    "Referer": "https://www.boulanger.com/ref/1216685",
    "x-api-key": d["clientSiteApiKey"],
}
site = "https://www.boulanger.com/api/referential/site-v4/sites/search"
bodies = [
    {"filters": [{"field": "zipCode", "value": "33700"}]},
    {"filter": [{"name": "zipCode", "value": "33700"}]},
    {"filter": {"searchCriteria": {"zipCode": "33700", "radius": 30}}},
    {"filter": {"geoLocation": {"zipCode": "33700", "countryCode": "FRA", "radius": 30000}}},
    {"filter": {"siteSearchCriteria": {"zipCode": "33700"}}},
    {"filter": {"nearBy": {"zipCode": "33700", "distance": 30000}}},
    {"filter": {"latitude": 44.8323, "longitude": -0.6817, "radius": 30000}},
]
for body in bodies:
    r = session.post(site, headers=site_hdr, json=body, timeout=15)
    if r.status_code == 200:
        print("SUCCESS", body, r.text[:1000])
    elif "SIT_003" not in r.text:
        print(body, r.status_code, r.text[:200])

# geography shops - try GET with query params
geo_hdr = {**site_hdr, "x-api-key": d["clientGeographyApiKey"]}
for url in [
    "https://www.boulanger.com/api/referential/geography-v3/shops?zipCode=33700",
    "https://www.boulanger.com/api/referential/geography-v3/shops/search?zipCode=33700&radius=30",
]:
    r = session.get(url, headers=geo_hdr, timeout=15)
    print("GET", url.split("geography-v3")[-1], r.status_code, r.text[:300])

# Search HTML for embedded store list / availability
for pat in [
    r'"availability"\s*:\s*\{[^}]{0,200}',
    r'"stores"\s*:\s*\[',
    r'clientSiteApiSearchEndpoint',
    r'local-stock/search',
]:
    if re.search(pat, h, re.I):
        m = re.search(pat, h, re.I)
        print("HTML match", pat, h[m.start() : m.start() + 300][:300])
