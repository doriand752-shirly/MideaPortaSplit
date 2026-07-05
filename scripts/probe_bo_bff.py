import re
import requests

js = requests.get(
    "https://www.boulanger.com/etc.clientlibs/boulanger-site/clientlibs/wpk.app/blg.product.b1c250982d62c42975a5.js",
    timeout=25,
).text
idx = js.find("bff-frontomc")
while idx >= 0:
    print(js[idx : idx + 200])
    idx = js.find("bff-frontomc", idx + 1)
    if idx > 5000:
        break

for pat in [r"shipping[^\"']{0,60}", r"localStock[^\"']{0,60}", r"getLocal[^\"']{0,60}"]:
    hits = sorted(set(re.findall(pat, js, re.I)))
    if hits:
        print(pat, hits[:10])
