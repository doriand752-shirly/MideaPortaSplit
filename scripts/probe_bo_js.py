import re
import requests

js = requests.get(
    "https://www.boulanger.com/etc.clientlibs/boulanger-site/clientlibs/wpk.app/blg.product.b1c250982d62c42975a5.js",
    timeout=25,
).text
print("js len", len(js))

for pat in [
    r'https://[^"\']+',
    r'/commerce/[^"\']+',
    r'STORE_AVAILABILITY[^;]{0,200}',
    r'availability[^"\']{0,80}',
    r'getStore[^"\']{0,80}',
    r'postalCode[^"\']{0,80}',
]:
    hits = re.findall(pat, js, re.I)
    if hits:
        print("\n", pat[:40], "count", len(hits))
        for h in sorted(set(hits))[:20]:
            if len(h) < 150:
                print(" ", h)

# find fetch/axios URLs near STORE_AVAILABILITY
idx = js.find("STORE_AVAILABILITY")
while idx >= 0:
    print("\nctx", js[idx:idx+400])
    idx = js.find("STORE_AVAILABILITY", idx + 1)
    if idx > 0 and js.count("STORE_AVAILABILITY") > 5:
        break
