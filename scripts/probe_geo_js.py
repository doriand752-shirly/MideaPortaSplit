import re
import requests

for js_url in [
    "https://www.boulanger.com/etc.clientlibs/boulanger-site/clientlibs/wpk.app/blg.product.b1c250982d62c42975a5.js",
    "https://www.boulanger.com/etc.clientlibs/boulanger-site/clientlibs/wpk.app/blg.chatbot.b9e4fa6caf1f1b8db902.js",
]:
    js = requests.get(js_url, timeout=25).text
    paths = sorted(set(re.findall(r"geography-v3[a-zA-Z0-9/_\-?=&.]+", js)))
    if paths:
        print(js_url.split("/")[-1][:30], paths[:20])

    for term in ["shops/search", "points-of-sale", "store/search", "localStock", "storeAvailability"]:
        if term in js:
            print("found", term, "in", js_url.split("/")[-1][:20])
