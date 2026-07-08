import re

import requests

from src.local_stores import geocode_postal_code, _haversine_km


def parse_city_page(url: str) -> list[tuple]:
    h = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20).text
    stores = []
    for chunk in h.split("<tr ")[1:]:
        if "px-4 py-3" not in chunk:
            continue
        texts = re.findall(r'class="px-4 py-3[^"]*"[^>]*>(.*?)</td>', chunk, re.S)
        if len(texts) < 3:
            continue
        name = re.sub(r"<[^>]+>", " ", texts[0])
        name = " ".join(name.split())
        city_line = re.sub(r"<[^>]+>", " ", texts[1])
        city_line = " ".join(city_line.split())
        dist_m = re.search(r"([\d,]+)\s*km", texts[2])
        in_stock = "En stock" in chunk
        if name and city_line:
            stores.append((name, city_line, dist_m.group(1) if dist_m else "?", in_stock))
    return stores


user_lat, user_lon, _ = geocode_postal_code("33000")

for city in ["bordeaux", "limoges", "la-rochelle", "toulouse", "nantes", "perigueux"]:
    u = f"https://climradar.fr/stock/portasplit/{city}"
    s = parse_city_page(u)
    print(city, len(s))
    for name, loc, dist, stock in s:
        cp_m = re.search(r"(\d{5})", loc)
        cp = cp_m.group(1) if cp_m else ""
        km = "?"
        if cp:
            lat, lon, _ = geocode_postal_code(cp)
            km = round(_haversine_km(user_lat, user_lon, lat, lon), 1)
        print(f"  {name} | {loc} | from33000={km}km | stock={stock}")
