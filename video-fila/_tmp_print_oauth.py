import sys
sys.path.insert(0, r"D:\logins-google")
import cofre
from playwright.sync_api import sync_playwright
em, e = cofre.conta(sys.argv[1])
with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{e['porta']}")
    pg = [x for x in br.contexts[0].pages if "accounts.google" in x.url][0]
    pg.screenshot(path=r"D:\video-fila\_tmp_oauth.png")
    print(pg.url[:120])
    print(" ".join(pg.inner_text("body").split())[:700])
