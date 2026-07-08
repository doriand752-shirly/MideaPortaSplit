import re

import requests

html = requests.get(
    "https://climradar.fr/stock/portasplit?cp=33000",
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=30,
).text

print("len", len(html))
print("En stock", html.count(">En stock<"))
print("Rupture", html.count(">Rupture<"))

pat = re.compile(
    r'href="/enseignes/([^"]+)">([^<]+)</a></div></td>'
    r'<td class="px-4 py-3 hidden sm:table-cell text-base-content/70">([^<]+)</td>'
    r'<td class="px-4 py-3 text-right hidden sm:table-cell text-base-content/70">'
    r"([\d,]+)\s*km</td>"
    r'<td class="px-4 py-3"><span[^>]*>.*?</span>(En stock|Rupture)</span>'
    r'.*?href="(https?://[^"]+)"',
    re.S,
)

for m in pat.finditer(html):
    retailer_slug, store_name, location, distance, status, url = m.groups()
    dist = float(distance.replace(",", "."))
    print(f"{status:8} {dist:5.1f}km {retailer_slug:12} {store_name:30} {location}")

print("total rows", len(pat.findall(html)))
