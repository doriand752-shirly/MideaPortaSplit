import json
import re

import requests

html = requests.get(
    "https://climradar.fr/produit/portasplit",
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=30,
).text

# Unescape RSC payload fragments containing store+entry pairs
pattern = re.compile(
    r'\\"store\\":\{.*?\\"entry\\":\{.*?\}\\}',
    re.S,
)
# Simpler: find entry blocks after storeId
entries = []
for m in re.finditer(
    r'\\"store\\":\{(\\"id\\":\\"[^"]+\\".*?)\\"entry\\":\{(\\"storeId\\":\\"[^"]+\\".*?)\\"lastSeenMinAgo\\":\d+',
    html,
):
    store_raw = "{" + m.group(1).replace('\\"', '"') + "}"
    entry_raw = "{" + m.group(2).replace('\\"', '"') + "}"
    try:
        # manual parse key fields
        name = re.search(r'"name":"([^"]+)"', store_raw.replace('\\"', '"'))
        retailer = re.search(r'"retailerId":"([^"]+)"', store_raw.replace('\\"', '"'))
        city = re.search(r'"city":"([^"]+)"', store_raw.replace('\\"', '"'))
        cp = re.search(r'"postalCode":"([^"]+)"', store_raw.replace('\\"', '"'))
        lat = re.search(r'"lat":([\d.-]+)', store_raw.replace('\\"', '"'))
        lon = re.search(r'"lon":([\d.-]+)', store_raw.replace('\\"', '"'))
        url = re.search(r'"address":"(https://[^"]+)"', store_raw.replace('\\"', '"'))
        status = re.search(r'"status":"([^"]+)"', entry_raw.replace('\\"', '"'))
        price = re.search(r'"price":(\d+)', entry_raw.replace('\\"', '"'))
        entries.append(
            {
                "retailer": retailer.group(1) if retailer else "",
                "name": name.group(1) if name else "",
                "city": city.group(1) if city else "",
                "postal": cp.group(1) if cp else "",
                "lat": float(lat.group(1)) if lat else None,
                "lon": float(lon.group(1)) if lon else None,
                "status": status.group(1) if status else "",
                "price": int(price.group(1)) if price else None,
                "url": url.group(1) if url else "",
            }
        )
    except Exception as e:
        print("parse err", e)

print("entries", len(entries))
for e in entries:
    if e["status"] == "en_stock" or "Merignac" in e["name"] or e["postal"].startswith("33"):
        print(e)
