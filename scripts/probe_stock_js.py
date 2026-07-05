import re
import requests

BASE = "https://climradar.fr"
html = requests.get(f"{BASE}/stock/portasplit?cp=33400", headers={"User-Agent": "Mozilla/5.0"}, timeout=30).text
chunks = sorted(set(re.findall(r"/_next/static/chunks/[^\"']+\.js", html)))
for c in chunks:
    if "page" in c or "stock" in c:
        print(c)

js_url = None
for c in chunks:
    if "page-f862ab24fb3253ab" in c:
        js_url = BASE + c
        break

if js_url:
    js = requests.get(js_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20).text
    print("js len", len(js))
    for m in re.finditer(r".{0,80}/api/stock.{0,200}", js):
        print("CTX:", m.group(0)[:280])
