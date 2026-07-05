import json
import re
import requests

h = requests.get("https://www.boulanger.com/ref/1216685", headers={"User-Agent": "Mozilla/5.0"}, timeout=25).text

# AEM data attributes
for pat in [r'data-store[^=]*="([^"]+)"', r'data-product[^=]*="([^"]+)"', r'window\.digitalData\s*=\s*(\{[\s\S]*?\});']:
    m = re.search(pat, h)
    if m:
        print("match", pat[:30], m.group(1)[:300])

# JSON with store and stock
for m in re.finditer(r'\{[^{}]{0,2000}"(?:store|magasin|availability)[^{}]{0,2000}\}', h, re.I):
    s = m.group(0)
    if "337" in s or "stock" in s.lower() or "avail" in s.lower():
        print("json blob", s[:400])
        print("---")

# Try boulanger local stock endpoint from page meta
for m in re.finditer(r'"localStock[^"]*"[^}]{0,500}', h, re.I):
    print("localStock", m.group(0)[:300])

# Castorama - search for product JSON in page
ca = requests.get(
    "https://www.castorama.fr/climatiseur-split-midea-reversible-3500w/8431312260509_CAFR.prd",
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=25,
).text

for m in re.finditer(r'window\.__[A-Z_]+__\s*=\s*(\{)', ca):
    print("window var at", m.start())

# search ean in script tags with store data
if "8431312260509" in ca:
    idx = 0
    count = 0
    while count < 5:
        idx = ca.find("8431312260509", idx + 1)
        if idx < 0:
            break
        snip = ca[idx:idx+500]
        if "store" in snip.lower() or "stock" in snip.lower():
            print("ean ctx", snip[:350])
            count += 1

# Castorama woosmap store finder - product might use separate API
# Try castorama product API from MFE manifest
for m in re.finditer(r'/_static/casto-browse-mfe/[^"\']+', ca):
    print("mfe", m.group(0)[:80])
