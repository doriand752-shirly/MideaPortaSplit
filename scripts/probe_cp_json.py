import re
import requests

from src.local_stores import _parse_climradar_store_entries, _unescape, _field

h = requests.get(
    "https://climradar.fr/stock/portasplit?cp=33000",
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=20,
).text

entries = _parse_climradar_store_entries(h)
print("json entries", len(entries))

for e in entries:
    name = e["name"].lower()
    if any(t in name or t in e.get("city", "").lower() for t in ("soyaux", "cognac", "angoul", "merignac", "bordeaux")):
        print(e)

# count by dept
from collections import Counter
depts = Counter()
for e in entries:
    cp = e.get("raw_postal", "")
    if cp and len(cp) >= 2:
        depts[cp[:2]] += 1
print("depts", dict(depts))

# show first 15 physical stores
for e in entries:
    if e.get("city") and "en ligne" not in e["name"].lower():
        print(e)
