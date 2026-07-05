import requests

from src.local_stores import _parse_climradar_city_html

for slug in ["bordeaux/leroy-merlin", "bordeaux", "la-rochelle", "limoges"]:
    url = f"https://climradar.fr/stock/portasplit/{slug}"
    h = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20).text
    rows = _parse_climradar_city_html(h)
    print(f"=== {slug} ({len(rows)} rows) ===")
    for r in rows:
        print(r["name"], "|", r["city"], r["raw_postal"], "|", r["in_stock"])
