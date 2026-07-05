import re
import requests

h = requests.get(
    "https://climradar.fr/stock/portasplit?cp=33400",
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=20,
).text

print("tr count", h.count("<tr "))
print("soyaux", "soyaux" in h.lower())
print("Merignac", "Merignac" in h or "merignac" in h.lower())

# find soyaux context
idx = h.lower().find("soyaux")
if idx >= 0:
    print(h[idx - 200 : idx + 300])

# try alternate row patterns
for pat in [
    r"Leroy Merlin[^<]{0,80}",
    r"Soyaux[^<]{0,40}",
    r"16800",
]:
    m = re.search(pat, h, re.I)
    if m:
        print("match", pat, m.group()[:100])

# sample tr structure
trs = h.split("<tr ")
print("first tr snippet", trs[2][:500] if len(trs) > 2 else "none")

# look for table structure
if "Merignac" in h:
    i = h.find("Merignac")
    print(h[i - 300 : i + 400])
