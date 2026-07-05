import re
import requests

js = requests.get(
    "https://www.boulanger.com/etc.clientlibs/boulanger-site/clientlibs/wpk.app/blg.product.b1c250982d62c42975a5.js",
    timeout=25,
).text

for cid in ["89835", "37101", "8359", "9093", "9635"]:
    m = re.search(rf'{cid}:"([a-f0-9]+)"', js)
    if m:
        h = m.group(1)
        url = f"https://www.boulanger.com/etc.clientlibs/boulanger-site/clientlibs/wpk.app/{cid}.{h}.js"
        r = requests.get(url, timeout=15)
        print(url.split(".com")[-1][:70], r.status_code, len(r.text))
        if r.status_code == 200 and len(r.text) > 500:
            for pat in [r"/api/[^\"']+", r"localStock", r"postalCode", r"storeInfos"]:
                if re.search(pat, r.text, re.I):
                    hits = re.findall(pat, r.text, re.I)
                    print("  ", pat, hits[:6])
