import requests

headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15",
    "Accept": "application/json",
}

for cid in ["8431312260509_01c", "8431312260509_02c", "8431312260509_03c"]:
    for store in ["1489", "1059", "0174"]:
        params = f"compositeOfferId={cid}&storeId={store}&postalCode=33700"
        url = f"https://www.castorama.fr/casto-browse-mfe/api/fulfilment-options?{params}"
        r = requests.get(url, headers=headers, timeout=15)
        print(cid, store, r.status_code)
        if r.status_code == 200:
            print(r.text[:800])
