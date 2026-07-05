import re
import requests

js = requests.get(
    "https://www.boulanger.com/etc.clientlibs/boulanger-site/clientlibs/wpk.app/blg.product.b1c250982d62c42975a5.js",
    timeout=25,
).text

for term in ["localStock", "storeAvailability", "geography-v3", "estimation-v1", "bff-frontomc"]:
    idx = 0
    found = 0
    while found < 5:
        i = js.find(term, idx)
        if i < 0:
            break
        print(f"\n=== {term} @ {i} ===")
        print(js[max(0, i - 120) : i + 200])
        idx = i + len(term)
        found += 1

paths = sorted(set(re.findall(r'"/api/[a-zA-Z0-9/_\-]+"', js)))
print("\nAPI paths sample:", paths[:40])
