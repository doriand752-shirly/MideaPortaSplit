import requests

headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15",
    "Accept": "application/json",
}
cid = "8431312260509_01c"
store = "1489"

for delivery in [[], ["CLICK_AND_COLLECT"], ["clickAndCollect"], ["COLLECT"]]:
    params = [("compositeOfferId", cid), ("storeId", store), ("postalCode", "33700")]
    for d in delivery:
        params.append(("delivery", d))
    r = requests.get(
        "https://www.castorama.fr/casto-browse-mfe/api/fulfilment-options",
        params=params,
        headers=headers,
        timeout=15,
    )
    print(delivery or "(none)", r.status_code, r.text[:400])
