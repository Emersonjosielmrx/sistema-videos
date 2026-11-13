"""sonda_studio.py - SOMENTE LEITURA. Abre o perfil dedicado no Chrome (CDP), vai ao YouTube Studio e diz se a sessao esta logada
e em qual canal. Nao envia nada. Uso: sonda_studio.py <pasta-do-perfil> <porta>"""
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
perfil, porta = sys.argv[1], int(sys.argv[2])
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
pasta = Path(r"D:\logins-google\chrome-profiles") / perfil
proc = subprocess.Popen([CHROME, f"--remote-debugging-port={porta}", f"--user-data-dir={pasta}", "--no-first-run",
                         "--no-default-browser-check", "--remote-allow-origins=*", "--window-size=1280,900",
                         "--window-position=-2000,0", "about:blank"])
for _ in range(30):
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{porta}/json/version", timeout=2)
        break
    except Exception:
        time.sleep(1)
with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
    ctx = br.contexts[0]
    pg = ctx.new_page()
    pg.goto("https://studio.youtube.com/", wait_until="domcontentloaded")
    time.sleep(8)
    print("URL:", pg.url)
    print("TITULO:", pg.title())
    pg.screenshot(path=str(Path(r"D:\manhwa-react\work") / f"sonda_{perfil}.png"))
    br.close()
proc.terminate()
