import sys, re, html, urllib.request
url, chaves = sys.argv[1], sys.argv[2:]
t = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read().decode()
t = re.sub(r"(?s)<(script|style|nav|header|footer)[^>]*>.*?</\1>", "", t)
t = html.unescape(re.sub(r"<[^>]+>", " ", t)); t = re.sub(r"[ \t]+", " ", t); t = re.sub(r"\n\s*\n+", "\n", t)
for k in chaves:
    for m in re.finditer(r"\n " + re.escape(k) + r" # \n", t):
        print("=====", k); print(t[m.start():m.start() + 900])
