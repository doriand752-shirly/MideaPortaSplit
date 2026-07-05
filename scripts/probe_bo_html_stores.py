import re
import requests

headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15"}
h = requests.get("https://www.boulanger.com/ref/1216685", headers=headers, timeout=25).text

for city in ["MERIGNAC", "Merignac", "BORDEAUX", "Pessac", "33700", "33000"]:
    idx = h.find(city)
    if idx >= 0:
        print(city, ":", re.sub(r"\s+", " ", h[idx - 60 : idx + 120])[:180])

# site API with filter wrapper from error messages - try filter object with type
import json
d = json.loads(re.search(r"var G_CONFIG = (\{[\s\S]*?\});", h).group(1))
site_hdr = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Origin": "https://www.boulanger.com",
    "Referer": "https://www.boulanger.com/ref/1216685",
    "x-api-key": d["clientSiteApiKey"],
}
for body in [
    {"filter": {"type": "NEARBY", "zipCode": "33700", "radius": 30000}},
    {"filter": {"type": "nearby", "zipCode": "33700"}},
    {"filter": {"searchType": "NEARBY", "zipCode": "33700"}},
    {"filter": {"criteria": {"zipCode": "33700", "radius": 30}}},
]:
    r = requests.post("https://www.boulanger.com/api/referential/site-v4/sites/search", headers=site_hdr, json=body, timeout=15)
    if r.status_code == 200:
        print("SITE OK", body, r.text[:800])
    elif "SIT_003" not in r.text:
        print(body, r.status_code, r.text[:150])
