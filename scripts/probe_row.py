import re

import requests

html = requests.get(
    "https://climradar.fr/stock/portasplit/bordeaux",
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=30,
).text

# Wider context for one row
idx = html.find("MERIGNAC 33700")
print(html[idx - 600 : idx + 400])
