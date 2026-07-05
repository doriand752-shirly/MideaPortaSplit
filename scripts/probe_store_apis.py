import re
import requests

CASTO_PRODUCT = "https://www.castorama.fr/climatiseur-split-midea-reversible-3500w/8431312260509_CAFR.prd"
EAN = "8431312260509"

headers_base = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
    "Accept-Language": "fr-FR,fr;q=0.9",
}

# Castorama - try with store cookies
for store_id in ["1489", "1059", "0174"]:
    h = {
        **headers_base,
        "Cookie": f"storeId={store_id}; favouriteStore={store_id}; selectedStore={store_id}",
    }
    r = requests.get(CASTO_PRODUCT, headers=h, timeout=25)
    text = r.text.lower()
    print(f"store {store_id} len {len(r.text)}")
    for term in ["en stock", "rupture", "indisponible", "disponible", "retrait", "1489"]:
        if term in text:
            print(f"  {term}: {text.count(term)}")

# Boulanger - fetch with store cookie
for store_code in ["121", "037", "F337"]:  # guess codes
    h = {
        **headers_base,
        "Cookie": f"storeCode={store_code}; favoriteStore={store_code}",
    }
    r = requests.get("https://www.boulanger.com/ref/1216685", headers=h, timeout=25)
    if "33700" in r.text or "merignac" in r.text.lower():
        print("boulanger store", store_code, "has merignac ref")

# Castorama internal - search __NEXT_DATA__ or window.__data
r = requests.get(CASTO_PRODUCT, headers=headers_base, timeout=25)
for m in re.finditer(r'__NEXT_DATA__[^>]*>([\s\S]*?)</script>', r.text):
    print("next data len", len(m.group(1)))

# Look for fulfilmentOptions in castorama page
if "fulfilment" in r.text.lower():
    idx = r.text.lower().find("fulfilment")
    print("fulfilment", r.text[idx:idx+300])

if "clickAndCollect" in r.text or "clickAndCollect" in r.text:
    idx = r.text.find("clickAndCollect")
    print("c&c", r.text[idx:idx+400])

# Try castorama graphql
gql_url = "https://www.castorama.fr/gateway/graphql"
query = {
    "query": "{ product(ean: \"8431312260509\") { name } }"
}
try:
    gr = requests.post(gql_url, json=query, headers={**headers_base, "Content-Type": "application/json"}, timeout=15)
    print("graphql", gr.status_code, gr.text[:300])
except Exception as e:
    print("gql err", e)

# castorama mobile api pattern from kingfisher
for url in [
    f"https://www.castorama.fr/gateway/graphql?operationName=Fulfilment&variables={{\"ean\":\"{EAN}\",\"storeId\":\"1489\"}}",
    "https://www.castorama.fr/api/graphql",
]:
    gr = requests.get(url, headers=headers_base, timeout=15)
    print("gql get", url.split(".fr")[-1][:50], gr.status_code, gr.text[:150])
