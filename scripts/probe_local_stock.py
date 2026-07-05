import re

import requests

html = requests.get(
    "https://climradar.fr/stock/portasplit/bordeaux",
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=30,
).text

print("En stock count", html.count(">En stock<"))
print("Rupture count", html.count(">Rupture<"))

pat = re.compile(
    r"([A-Z][A-Za-z' -]+ 33\d{3})</td>"
    r'<td class="px-4 py-3 text-right hidden sm:table-cell text-base-content/70">'
    r"([\d,]+)\s*km</td>"
    r'<td class="px-4 py-3"><span[^>]*>.*?</span>(En stock|Rupture)</span>'
)

for m in pat.finditer(html):
    print(m.group(1), m.group(2) + " km", m.group(3))

# Also try retailer-specific pages
for retailer in ["leroy-merlin", "castorama", "boulanger", "darty"]:
    url = f"https://climradar.fr/stock/portasplit/bordeaux/{retailer}"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    print(retailer, r.status_code, ">En stock<" in r.text, ">Rupture<" in r.text)
