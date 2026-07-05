import re
import requests

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
PRODUCT = (
    "https://www.castorama.fr/climatiseur-split-midea-reversible-3500w/"
    "8431312260509_CAFR.prd"
)
h = requests.get(PRODUCT, headers={"User-Agent": UA, "Accept": "text/html"}, timeout=25).text
i = h.find("stores/CAFR")
w = h[i : i + 800] if i >= 0 else h
m = re.search(r'[Aa]uthorization\\?"\s*:\s*\\?"([^"\\]{20,200})', w)
print("token found", bool(m))
if not m:
    raise SystemExit(1)
tok = m.group(1)
r = requests.get(
    "https://api.kingfisher.com/v1/mobile/stores/CAFR",
    params={
        "nearLatLong": "44.84,-0.58",
        "page[size]": 10,
        "include": "clickAndCollect,stock",
        "filter[ean]": "8431312260509",
    },
    headers={"User-Agent": UA, "Authorization": tok, "Accept": "application/json"},
    timeout=25,
)
print("api", r.status_code)
data = r.json().get("data", [])
print("stores", len(data))
for s in data[:5]:
    a = s.get("attributes", {})
    st = a.get("store", {})
    p = (a.get("stock", {}).get("products") or [{}])[0]
    print(
        " ",
        st.get("name"),
        st.get("geoCoordinates", {}).get("postalCode"),
        p.get("stockLevel"),
        p.get("quantity"),
    )
