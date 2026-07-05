import json
import re
import requests

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15"})

# Get G_CONFIG keys
h = session.get("https://www.boulanger.com/ref/1216685", timeout=25).text
d = json.loads(re.search(r"var G_CONFIG = (\{[\s\S]*?\});", h).group(1))
print("G_CONFIG keys with api/local/store:")
for k in sorted(d.keys()):
    if any(x in k.lower() for x in ["api", "local", "store", "stock", "geo", "estim", "bff"]):
        v = d[k]
        if isinstance(v, str) and len(v) > 60:
            v = v[:60] + "..."
        print(f"  {k}: {v}")

# geography POST cities search
geo_hdr = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Origin": "https://www.boulanger.com",
    "Referer": "https://www.boulanger.com/ref/1216685",
    "x-api-key": d["clientGeographyApiKey"],
}
geo = "https://www.boulanger.com/api/referential/geography-v3"
r = session.post(geo + "/cities/search", headers=geo_hdr, json={"filter": {"zipCode": "33700"}}, timeout=15)
print("\ncities 33700:", r.status_code, r.text[:500])

# Try to find shops endpoint from runtime/webpack
runtime = session.get(
    "https://www.boulanger.com/etc.clientlibs/boulanger-site/clientlibs/wpk.app/runtime.b1c250982d62c42975a5.js",
    timeout=25,
).text
for pat in [r"geography-v3[^\"']{0,80}", r"local-stock[^\"']{0,80}", r"localStock[^\"']{0,80}"]:
    hits = sorted(set(re.findall(pat, runtime)))
    if hits:
        print("\nruntime", pat, hits[:10])

product_js = session.get(
    "https://www.boulanger.com/etc.clientlibs/boulanger-site/clientlibs/wpk.app/blg.product.b1c250982d62c42975a5.js",
    timeout=25,
).text
# Find chunk hash map
m = re.search(r"89835:\"([a-f0-9]+)\"", product_js)
print("\n89835 hash", m.group(1) if m else "NOT FOUND")
if m:
    url = f"https://www.boulanger.com/etc.clientlibs/boulanger-site/clientlibs/wpk.app/89835.{m.group(1)}.js"
    cr = session.get(url, timeout=25)
    print("chunk", cr.status_code, len(cr.text))
    if cr.status_code == 200:
        for term in ["post", "get", "fetch", "api/", "local", "shop", "store"]:
            if term in cr.text.lower():
                pass
        apis = sorted(set(re.findall(r'["\'](/api/[^"\']+)["\']', cr.text)))
        print("API paths in chunk:", apis[:20])
        # search endpoint strings
        for pat in [r"localStock[A-Za-z]*", r"/[a-z-]+/availability", r"shops/[a-z]+"]:
            hits = sorted(set(re.findall(pat, cr.text)))
            if hits:
                print(pat, hits[:15])

# Search entire product bundle for geography paths
geo_paths = sorted(set(re.findall(r'geography-v3/[a-zA-Z0-9/_-]+', product_js)))
print("\ngeography paths in product js:", geo_paths[:20])

est_paths = sorted(set(re.findall(r'estimation-v1/[a-zA-Z0-9/_-]+', product_js)))
print("estimation paths:", est_paths[:20])

bff_paths = sorted(set(re.findall(r'bff-frontomc-v1/[a-zA-Z0-9/_-]+', product_js)))
print("bff paths:", bff_paths[:20])
