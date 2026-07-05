import requests

js = requests.get(
    "https://www.castorama.fr/_static/casto-browse-mfe/v0-677-1/get-fulfilment-options-CjZyTRWm.js",
    timeout=25,
).text

for term in [
    "CLICK_AND_COLLECT",
    "AVAILABLE",
    "UNAVAILABLE",
    "GLOBAL",
    "fulfilled",
    "included",
    "clickCollect",
    "isProductAvailable",
]:
    count = js.count(term)
    if count:
        i = js.find(term)
        print(f"\n{term} ({count}):", js[max(0, i - 40) : i + 100])

# Save snippet around Se function that parses results
idx = js.find("resultWithStore")
print("\nresultWithStore:", js[idx : idx + 500])
