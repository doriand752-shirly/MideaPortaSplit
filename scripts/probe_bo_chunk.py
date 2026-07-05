import re
import requests

base_js = requests.get(
    "https://www.boulanger.com/etc.clientlibs/boulanger-site/clientlibs/wpk.app/blg.product.b1c250982d62c42975a5.js",
    timeout=25,
).text

# find chunk 37101 file
m = re.search(r'n\.e\(8359\)\.then\(n\.bind\(n,(\d+)\)\)', base_js)
print("store avail chunk id", m.group(1) if m else "none")

# webpack public path
pm = re.search(r'p\.p="([^"]+)"', base_js) or re.search(r'publicPath:"([^"]+)"', base_js)
print("public path", pm.group(1) if pm else "none")

# list chunk files referenced
chunks = sorted(set(re.findall(r'(\d+)\.([a-f0-9]+)\.js', base_js)))
print("chunk refs", len(chunks))

# try common chunk path for 37101
for path in [
    "/etc.clientlibs/boulanger-site/clientlibs/wpk.app/37101.b1c250982d62c42975a5.js",
    "/etc.clientlibs/boulanger-site/clientlibs/wpk.app/chunk.37101.js",
]:
    r = requests.get("https://www.boulanger.com" + path, timeout=15)
    print(path, r.status_code, len(r.text))
    if r.status_code == 200 and len(r.text) > 1000:
        for pat in [r'/commerce/[^"\']+', r'availability[^"\']{0,60}', r'fetch\([^)]+\)']:
            hits = re.findall(pat, r.text, re.I)
            if hits:
                print(" hits", hits[:10])

# parse runtime chunk for mapping
runtime = requests.get(
    "https://www.boulanger.com/etc.clientlibs/boulanger-site/clientlibs/wpk.app/runtime.b1c250982d62c42975a5.js",
    timeout=15,
)
print("runtime", runtime.status_code, len(runtime.text))
if runtime.status_code == 200:
    if "37101" in runtime.text:
        idx = runtime.text.find("37101")
        print(runtime.text[idx-100:idx+200])
