"""
Teste AUTOMATIZADO de comentarios com conta nova emersonjosiel2026
"""
import sys
import time
import random
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR / "engage_modules"))
sys.path.insert(0, str(BASE_DIR / "shared"))

from playwright.sync_api import sync_playwright
from google_session import get_profile_dir, PORT_MAP
from engagement import do_comment
import subprocess

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
TEST_ACCOUNT = "emersonjosiel2026"
TEST_VIDEO = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
TEST_COMMENT = "Teste automatizado - bot funcionando com conta nova!"

print(f"[AUTO-TEST] Conta: {TEST_ACCOUNT}")
print(f"[AUTO-TEST] Video: {TEST_VIDEO}")

profile_dir = get_profile_dir(TEST_ACCOUNT)
port = PORT_MAP.get(TEST_ACCOUNT, 9348)

print(f"[AUTO-TEST] Perfil: {profile_dir}")
print(f"[AUTO-TEST] Porta CDP: {port}")

# Launch Chrome
proc = subprocess.Popen([
    CHROME_PATH,
    f"--user-data-dir={profile_dir}",
    f"--remote-debugging-port={port}",
    "--headless=new",
    "--no-first-run",
    "--disable-gpu",
    "--mute-audio",
    "about:blank"
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

time.sleep(5)
print(f"[AUTO-TEST] Chrome lancado (PID={proc.pid})")

try:
    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()

        print(f"[AUTO-TEST] Navegando...")
        page.goto(TEST_VIDEO, timeout=30000, wait_until="domcontentloaded")
        time.sleep(3)

        print(f"[AUTO-TEST] Tentando comentar com funcao do_comment()...")

        # Usar a função real do bot
        success = do_comment(page, TEST_COMMENT)

        print()
        print("="*60)
        if success:
            print("SUCCESS! COMENTARIO AUTOMATIZADO FUNCIONA!")
            print("="*60)
            print()
            print(f"Comentario postado: {TEST_COMMENT}")
            print()
            print("CONCLUSAO:")
            print("- Conta nova (emersonjosiel2026) NAO tem shadowban")
            print("- Bot consegue comentar automaticamente")
            print("- Pronto para adicionar ao pool de producao")
        else:
            print("FAIL - Comentario automatizado nao funcionou")
            print("="*60)
            print()
            print("CONCLUSAO:")
            print("- Precisa debug adicional")
            print("- Verificar logs [COMMENT-DEBUG] acima")
        print()

        browser.close()

finally:
    print("[AUTO-TEST] Encerrando Chrome...")
    proc.terminate()
    time.sleep(2)
    if proc.poll() is None:
        proc.kill()

print("[AUTO-TEST] Teste completo!")
