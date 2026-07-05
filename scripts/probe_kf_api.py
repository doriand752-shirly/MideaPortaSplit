import requests

headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15",
    "Accept": "application/json",
    "Accept-Language": "fr-FR,fr;q=0.9",
}

EAN = "8431312260509"
SKU = "1216685"
LM_ID = "93857579"

tests = [
    ("casto fulfilment", "GET", f"https://kf.api.castorama.fr/fulfilment/v1/products/{EAN}/stores/1489"),
    ("casto product", "GET", f"https://kf.api.castorama.fr/product/v1/products/{EAN}"),
    ("casto stock", "GET", f"https://kf.api.castorama.fr/stock/v1/products/{EAN}?storeId=1489"),
    ("casto cnc", "GET", f"https://kf.api.castorama.fr/click-and-collect/v1/products/{EAN}/stores/1489"),
    ("lm product", "GET", f"https://api.leroymerlin.fr/v3/products/{LM_ID}"),
    ("lm stock", "GET", f"https://api.leroymerlin.fr/v3/products/{LM_ID}/stores?storeIds=063"),
    ("lm merignac", "GET", "https://api.leroymerlin.fr/v3/stores/063"),
    ("bo api", "GET", f"https://api.boulanger.com/offer/merch-v3/products/{SKU}"),
    ("darty", "GET", "https://www.darty.com/nav/extra/ajax/productAvailability?codic=4071234"),
]

for name, method, url in tests:
    try:
        r = requests.request(method, url, headers=headers, timeout=15)
        print(name, r.status_code, r.text[:250].replace("\n", " "))
    except Exception as e:
        print(name, "ERR", e)
    print("---")
