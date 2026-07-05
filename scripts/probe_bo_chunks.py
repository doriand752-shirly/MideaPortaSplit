import re
import requests

js = requests.get(
    "https://www.boulanger.com/etc.clientlibs/boulanger-site/clientlibs/wpk.app/blg.product.b1c250982d62c42975a5.js",
    timeout=25,
).text

for cid in ["9093", "89835", "8359", "9635", "37101"]:
    m = re.search(rf'{cid}:"([a-f0-9]+)"', js)
    if not m:
        print(cid, "hash NOT FOUND")
        continue
    h = m.group(1)
    url = f"https://www.boulanger.com/etc.clientlibs/boulanger-site/clientlibs/wpk.app/{cid}.{h}.js"
    r = requests.get(url, timeout=15)
    print(cid, r.status_code, len(r.text), url.split("/")[-1])
    if r.status_code == 200 and len(r.text) > 500:
        text = r.text
        for pat in [r"/api/[^\"']+", r"local-stock", r"postalCode", r"siteCode", r"zipCode", r"promise"]:
            hits = sorted(set(re.findall(pat, text)))
            if hits:
                print(" ", pat, hits[:10])

# Also try named chunk blg.act.local-stock
for m in re.finditer(r"9093:\"([a-f0-9]+)\"", js):
    pass
named = re.findall(r"blg\.act\.local-stock\.([a-f0-9]+)\.js", js)
print("named chunks", named[:5])
