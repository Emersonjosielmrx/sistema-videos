"""
Teste HEADLESS de comentario com conta ANTIGA (fabricadeautomacoes0)
pra confirmar que o problema era so aulacomia (canal banido).
"""
import sys
import time
from pathlib import Path
import subprocess

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR / "engage_modules"))
sys.path.insert(0, str(BASE_DIR / "shared"))

from playwright.sync_api import sync_playwright
from google_session import get_profile_dir, PORT_MAP
import importlib
import engage_modules.engagement as eng
do_comment = eng.do_comment

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
ACCOUNT = "fabricadeautomacoes0"
TEST_VIDEO = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
COMMENT = "Teste headless bot OK"

profile_dir = get_profile_dir(ACCOUNT)
port = PORT_MAP.get(ACCOUNT, 9338)

print(f"[TEST] Conta: {ACCOUNT}")
print(f"[TEST] Perfil: {profile_dir}")
print(f"[TEST] Porta CDP: {port}")
print(f"[TEST] Modo: HEADLESS")

proc = subprocess.Popen([
    CHROME_PATH,
    f"--user-data-dir={profile_dir}",
    f"--remote-debugging-port={port}",
    "--headless=new",
    "--no-first-run",
    "--disable-gpu",
    "--mute-audio",
    "--disable-software-rasterizer",
    "--disable-dev-shm-usage",
    "--disable-extensions",
    "--no-sandbox",
    "--window-size=1920,1080",
    "about:blank",
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

time.sleep(5)
print(f"[TEST] Chrome lancado (PID={proc.pid})")

try:
    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()

        print(f"[TEST] Navegando para {TEST_VIDEO}")
        page.goto(TEST_VIDEO, timeout=60000, wait_until="domcontentloaded")
        time.sleep(5)

        print(f"[TEST] Chamando do_comment()...")
        success = do_comment(page, COMMENT)

        print()
        print("=" * 60)
        if success:
            print("SUCESSO! Comentario headless FUNCIONA com conta antiga!")
            print("O problema era SOMENTE a aulacomia (canal banido)")
        else:
            print("FALHOU - do_comment retornou False")
            print("Precisa investigar mais o codigo")
        print("=" * 60)

        browser.close()

finally:
    print("[TEST] Encerrando Chrome...")
    proc.terminate()
    time.sleep(2)
    if proc.poll() is None:
        proc.kill()

print("[TEST] Teste completo!")
