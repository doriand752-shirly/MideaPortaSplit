import json
import math
import sys

import requests

BASE = "https://climradar.fr"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PRODUCT_ID = "portasplit"
USER_CP = "33000"
RADIUS_KM = 100


def haversine(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def geocode(cp):
    r = requests.get(
        "https://api-adresse.data.gouv.fr/search/",
        params={"q": cp, "limit": 1},
        timeout=15,
    )
    feat = r.json()["features"][0]
    lon, lat = feat["geometry"]["coordinates"]
    return lat, lon


data = requests.get(f"{BASE}/api/stock", headers=HEADERS, timeout=60).json()
stores = {s["id"]: s for s in data["stores"]}
retailers = {r["id"]: r for r in data["retailers"]}

# Online FR offers
print("=== Online FR ===")
for store_id, entries in data["stockByStore"].items():
    store = stores.get(store_id)
    if not store or store.get("channel") != "online" or store.get("country") != "FR":
        continue
    entry = next((e for e in entries if e["productId"] == PRODUCT_ID), None)
    if not entry:
        continue
    ret = retailers.get(store["retailerId"], {})
    print(
        f"{ret.get('name', store['retailerId']):15} "
        f"{entry['status']:12} {entry.get('price')} "
        f"last={entry.get('lastSeenMinAgo')}min"
    )

# Local stores near 33000
ulat, ulon = geocode(USER_CP)
print(f"\n=== Stores near {USER_CP} ({RADIUS_KM}km) ===")
near = []
for store_id, entries in data["stockByStore"].items():
    store = stores.get(store_id)
    if not store or store.get("channel") != "store" or store.get("country") != "FR":
        continue
    entry = next((e for e in entries if e["productId"] == PRODUCT_ID), None)
    if not entry:
        continue
    dist = haversine(ulat, ulon, store["lat"], store["lon"])
    if dist > RADIUS_KM:
        continue
    near.append((dist, store, entry))

near.sort(key=lambda x: (x[2]["status"] != "en_stock", x[0]))
print("total", len(near), "instock", sum(1 for _, _, e in near if e["status"] == "en_stock"))
for dist, store, entry in near[:15]:
    ret = retailers.get(store["retailerId"], {})
    mark = "OK" if entry["status"] == "en_stock" else "--"
    print(
        f"{mark} {dist:5.1f}km {ret.get('name','')[:12]:12} "
        f"{store['name'][:35]:35} {store['postalCode']:6} {entry.get('price')}"
    )
