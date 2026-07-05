import json
import re
import requests

CASTO = "https://www.castorama.fr/climatiseur-split-midea-reversible-3500w/8431312260509_CAFR.prd"
BO = "https://www.boulanger.com/ref/1216685"

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
    "Accept-Language": "fr-FR,fr;q=0.9",
}

for name, url in [("castorama", CASTO), ("boulanger", BO)]:
    h = requests.get(url, headers=headers, timeout=25).text
    print("\n===", name, "===")
    # JSON blobs with store + stock
    for m in re.finditer(r'"storeId"\s*:\s*"([^"]+)"[^}]{0,300}', h):
        snip = m.group(0)[:200]
        if "stock" in snip.lower() or "avail" in snip.lower():
            print("storeId blob:", snip)

    for m in re.finditer(r'"postalCode"\s*:\s*"33700"[^}]{0,400}', h):
        print("33700:", m.group(0)[:250])

    for m in re.finditer(r'"33700"[^}]{0,200}(?:IN_STOCK|AVAILABLE|available|inStock|enStock)', h, re.I):
        print("33700 stock:", m.group(0)[:200])

    # next data
    if "33700" in h:
        idx = h.find("33700")
        print("33700 context:", re.sub(r"\s+", " ", h[idx - 100 : idx + 200])[:300])

    # ld+json
    for m in re.finditer(r'<script type="application/ld\+json">([\s\S]*?)</script>', h):
        try:
            data = json.loads(m.group(1))
            if isinstance(data, dict) and "offers" in str(data).lower():
                print("ld+json keys", list(data.keys())[:10])
        except json.JSONDecodeError:
            pass
