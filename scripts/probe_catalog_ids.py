import re
import requests

headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15"}

CASTO_MAGASINS = [
    ("ca-merignac", "https://www.castorama.fr/magasin/merignac"),
    ("ca-begles", "https://www.castorama.fr/magasin/begles"),
    ("ca-bordeaux", "https://www.castorama.fr/magasin/bordeaux"),
    ("ca-la-rochelle", "https://www.castorama.fr/magasin/la-rochelle"),
    ("ca-angouleme", "https://www.castorama.fr/magasin/angouleme"),
    ("ca-perigueux", "https://www.castorama.fr/magasin/perigueux"),
]

for sid, url in CASTO_MAGASINS:
    r = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
    m = re.search(r"/store/(\d+)", r.url)
    ids = re.findall(r'"storeId"\s*:\s*"(\d+)"', r.text[:20000])
    print(sid, "->", m.group(1) if m else "?", "url", r.url.split(".fr")[-1][:45], "ids", sorted(set(ids))[:3])

LM_SLUGS = [
    ("lm-merignac", "https://www.leroymerlin.fr/magasins/merignac-bordeaux.html"),
    ("lm-gradignan", "https://www.leroymerlin.fr/magasins/gradignan-bordeaux.html"),
    ("lm-bordeaux-lac", "https://www.leroymerlin.fr/magasins/bordeaux-lac.html"),
]
for sid, url in LM_SLUGS:
    r = requests.get(url, headers=headers, timeout=20)
    slug = url.split("/magasins/")[-1].replace(".html", "")
    store_id = re.findall(r'"storeId"\s*:\s*"?(\d+)"?', r.text[:30000])
    print("LM", sid, slug, "status", r.status_code, "storeIds", store_id[:3])
