import requests

from src.local_stores import _parse_climradar_city_html, geocode_postal_code, _haversine_km

HUBS = [
    "perigueux", "agen", "mont-de-marsan", "libourne", "angouleme",
    "cognac", "royan", "rochefort", "chatellerault", "poitiers",
    "brive", "tarbes", "montauban",
]

user_lat, user_lon, _ = geocode_postal_code("33400")

for slug in HUBS:
    url = f"https://climradar.fr/stock/portasplit/{slug}"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    if r.status_code != 200 or len(r.text) < 10000:
        continue
    rows = _parse_climradar_city_html(r.text)
    if not rows:
        continue
    print(f"=== {slug} ({len(rows)}) ===")
    for row in rows:
        cp = row["raw_postal"]
        try:
            lat, lon, dept = geocode_postal_code(cp)
            d = _haversine_km(user_lat, user_lon, lat, lon)
        except Exception:
            d = -1
        if d <= 200 or any(t in row["name"].lower() for t in ("soyaux", "cognac", "angoul")):
            print(f"  {row['name']} | {row['city']} {cp} | {d:.0f}km | stock={row['in_stock']}")
