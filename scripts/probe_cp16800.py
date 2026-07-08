import re

import requests

from src.local_stores import _parse_climradar_city_html, geocode_postal_code, _haversine_km

h = requests.get(
    "https://climradar.fr/stock/portasplit?cp=16800",
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=20,
).text
print("len", len(h))
print("soyaux", "soyaux" in h.lower())

rows = _parse_climradar_city_html(h)
print("rows", len(rows))
for r in rows:
    if any(t in (r["name"] + r["city"]).lower() for t in ("soyaux", "cognac", "angoul")):
        print(r)

user_lat, user_lon, _ = geocode_postal_code("33000")
for r in rows:
    if "soyaux" in r["name"].lower() or "cognac" in r["name"].lower():
        cp = r["raw_postal"]
        lat, lon, _ = geocode_postal_code(cp)
        d = _haversine_km(user_lat, user_lon, lat, lon)
        print("distance from 33000", d, r)

# also cp=33000
h2 = requests.get(
    "https://climradar.fr/stock/portasplit?cp=33000",
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=20,
).text
rows2 = _parse_climradar_city_html(h2)
print("cp33000 rows", len(rows2))
for r in rows2:
    if any(t in (r["name"] + r["city"]).lower() for t in ("soyaux", "cognac", "angoul")):
        print(r)
