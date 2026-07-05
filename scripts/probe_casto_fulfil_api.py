import requests

js = requests.get(
    "https://www.castorama.fr/_static/casto-browse-mfe/v0-677-1/get-fulfilment-options-CjZyTRWm.js",
    timeout=25,
).text

idx = js.find("/api/fulfilment-options")
print(js[max(0, idx - 400) : idx + 400])

headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15",
    "Accept": "application/json",
    "Accept-Language": "fr-FR,fr;q=0.9",
}

EAN = "8431312260509"
for store_id in ["1489", "1059", "0174"]:
    for qs in [
        f"ean={EAN}&storeId={store_id}",
        f"productEan={EAN}&storeId={store_id}",
        f"ean={EAN}&store={store_id}",
    ]:
        url = f"https://www.castorama.fr/api/fulfilment-options?{qs}"
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            print("\nOK", qs, r.text[:600])
        elif r.status_code != 404:
            print(qs, r.status_code, r.text[:200])
