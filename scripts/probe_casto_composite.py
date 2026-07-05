import re
import requests

headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15",
    "Accept": "application/json",
}
EAN = "8431312260509"
PATH = f"climatiseur-split-midea-reversible-3500w/{EAN}_CAFR.prd"

h = requests.get(f"https://www.castorama.fr/store/1489/{PATH}", headers=headers, timeout=25).text

cids = sorted(set(re.findall(r'"compositeOfferId"\s*:\s*"([^"]+)"', h)))
print("compositeOfferIds", cids[:10])

for cid in cids[:3]:
    for store in ["1489", "1059"]:
        params = f"compositeOfferId={cid}&storeId={store}&postalCode=33700"
        url = f"https://www.castorama.fr/casto-browse-mfe/api/fulfilment-options?{params}"
        r = requests.get(url, headers=headers, timeout=15)
        print("\n", cid, store, r.status_code, r.text[:600])
