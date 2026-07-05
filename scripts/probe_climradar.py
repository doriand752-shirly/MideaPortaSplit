import requests

html = requests.get(
    "https://climradar.fr/produit/portasplit",
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=30,
).text

idx = html.find('"name":"Darty"')
print(html[idx - 200 : idx + 400])
