import sys
sys.path.insert(0, ".")

from src.local_stores import _parse_climradar_store_entries, _parse_climradar_city_html, fetch_local_stores
import requests

cp = requests.get(
    "https://climradar.fr/stock/portasplit?cp=33400",
    headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15"},
    timeout=25,
).text
entries = _parse_climradar_store_entries(cp)
print("cp33400 json entries", len(entries))
for e in entries[:8]:
    print(e)

city = requests.get(
    "https://climradar.fr/stock/portasplit/bordeaux/leroy-merlin",
    headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15"},
    timeout=25,
).text
rows = _parse_climradar_city_html(city)
print("\nbordeaux lm city rows", len(rows))
for r in rows[:5]:
    print(r)

stores = fetch_local_stores("33400", 200)
print("\nfetch_local_stores total", len(stores), "in stock", sum(1 for s in stores if s.in_stock))
