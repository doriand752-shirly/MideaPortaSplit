import re
import requests

headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15",
}
EAN = "8431312260509"
PATH = f"climatiseur-split-midea-reversible-3500w/{EAN}_CAFR.prd"
url = f"https://www.castorama.fr/store/1489/{PATH}"
h = requests.get(url, headers=headers, timeout=25).text

for pat in [
    r'self\.__next_f\.push\(\[1,"([^"]{0,500})"',
    r'"fulfilment[^"]*"\s*:\s*[^,]{0,100}',
    r'clickAndCollect[^\\]{0,200}',
    r'\\"inStock\\":\\?(true|false)',
    r'\\"availability\\":\\?"([^\\"]+)\\?"',
    r'"clickCollectAvailability"\s*:\s*"([^"]+)"',
]:
    hits = re.findall(pat, h)
    if hits:
        print(pat[:40], len(hits), hits[0][:200] if isinstance(hits[0], str) else hits[0])

# Find all JSON-like stock strings
for m in re.finditer(r'.{0,30}(?:inStock|stockLevel|availabilityStatus).{0,80}', h, re.I):
    s = m.group(0)
    if "8431312260509" in s or "1489" in s or "click" in s.lower():
        print("ctx:", s[:120])

print("next_f count", h.count("__next_f"))
print("8431312260509 count", h.count(EAN))
