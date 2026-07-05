import json
import re
import requests

h = requests.get("https://www.boulanger.com/ref/1216685", headers={"User-Agent": "Mozilla/5.0"}, timeout=25).text
d = json.loads(re.search(r"var G_CONFIG = (\{[\s\S]*?\});", h).group(1))
api_key = d.get("clientEstimationApiKey") or d.get("clientBffApiKey")
print("estimation key", api_key[:20] if api_key else None)

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
    "Accept": "application/json",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Origin": "https://www.boulanger.com",
    "Referer": "https://www.boulanger.com/ref/1216685",
    "x-api-key": api_key or "",
}

base = "https://www.boulanger.com/api/commerce/estimation-v1"
for path in [
    "/products/1216685/stores?postalCode=33700",
    "/products/1216685/availability?postalCode=33700",
    "/availability/stores?sku=1216685&postalCode=33700",
    "/store-availability?productId=1216685&postalCode=33700",
]:
    r = requests.get(base + path, headers=headers, timeout=15)
    print(path, r.status_code, r.text[:300])
    print("---")

# POST body variants
for body in [
    {"productId": "1216685", "postalCode": "33700"},
    {"skuId": "1216685", "postalCode": "33700", "shippingMethod": "STORE"},
    {"products": [{"skuId": "1216685"}], "postalCode": "33700"},
]:
    r = requests.post(base + "/availability", headers={**headers, "Content-Type": "application/json"}, json=body, timeout=15)
    print("POST", body, r.status_code, r.text[:300])
    print("---")

# geography shops near postal
geo_key = d.get("clientGeographyApiKey")
gh = {**headers, "x-api-key": geo_key or api_key or ""}
for path in [
    "https://www.boulanger.com/api/referential/geography-v3/shops/search?postalCode=33700&radius=30",
    "https://www.boulanger.com/api/referential/geography-v3/cities/search?postalCode=33700",
]:
    r = requests.get(path, headers=gh, timeout=15)
    print("geo", path.split(".com")[-1][:60], r.status_code, r.text[:400])
