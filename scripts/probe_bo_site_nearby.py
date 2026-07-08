import json
import re
import requests

headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15"}
h = requests.get("https://www.boulanger.com/ref/1216685", headers=headers, timeout=25).text
d = json.loads(re.search(r"var G_CONFIG = (\{[\s\S]*?\});", h).group(1))
site_hdr = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Origin": "https://www.boulanger.com",
    "Referer": "https://www.boulanger.com/ref/1216685",
    "x-api-key": d["clientSiteApiKey"],
}
base = "https://www.boulanger.com/api/referential/site-v4/sites/search"

filters = [
    {"filter": {"type": "NEARBY", "zipCode": "33700", "radius": 50}},
    {"filter": {"type": "NEARBY", "cityCode": "33281", "radius": 50}},
    {"filter": {"type": "NEARBY", "latitude": 44.8323, "longitude": -0.6817, "radius": 50}},
    {"filter": {"type": "NEARBY", "zipCode": "33000", "radius": 100}},
]
for body in filters:
    r = requests.post(base, headers=site_hdr, json=body, timeout=15)
    n = len(r.json().get("results", [])) if r.status_code == 200 else -1
    print(body["filter"], "->", r.status_code, "count", n)
    if n > 0:
        print(r.text[:1000])
