import json
import re
import requests

h = requests.get("https://www.boulanger.com/ref/1216685", headers={"User-Agent": "Mozilla/5.0"}, timeout=25).text
scripts = re.findall(r'src="(/etc\.clientlibs[^"]+\.js[^"]*)"', h)

paths = set()
for s in scripts:
    js = requests.get("https://www.boulanger.com" + s, timeout=25).text
    for p in re.findall(r'"/api/[^"]+"', js):
        pl = p.lower()
        if any(k in pl for k in ("avail", "store", "shop", "stock", "estim", "local")):
            paths.add(p.strip('"'))

print("api paths:")
for p in sorted(paths):
    print(" ", p)

d = json.loads(re.search(r"var G_CONFIG = (\{[\s\S]*?\});", h).group(1))
key = d.get("clientMerchApiKey")
headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "x-api-key": key,
    "Origin": "https://www.boulanger.com",
    "Referer": "https://www.boulanger.com/ref/1216685",
}
for path in ["/products/1216685", "/products/1216685/availability", "/products/1216685/stores"]:
    r = requests.get("https://www.boulanger.com/api/offer/merch-v3" + path, headers=headers, timeout=15)
    print("merch", path, r.status_code, r.text[:300])
