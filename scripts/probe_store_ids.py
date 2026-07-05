import re
import requests

headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15"}

for name, url in [
    ("merignac", "https://www.castorama.fr/store/1489"),
    ("begles", "https://www.castorama.fr/magasin/begles"),
]:
    r = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
    print(name, r.url.split(".fr")[-1][:50])

for url in [
    "https://www.boulanger.com/magasins/bordeaux",
    "https://www.boulanger.com/magasins/merignac",
]:
    r = requests.get(url, headers=headers, timeout=20)
    hits = re.findall(r'"siteCode"\s*:\s*"(\d+)"', r.text)
    print("BO", url.split("/")[-1], hits[:5])
