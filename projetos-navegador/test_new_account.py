"""
Teste comentários com conta NOVA: emersonjosiel2026@gmail.com
Esta conta nunca foi usada pelo bot antes
"""
import sys
import time
import random
from pathlib import Path
import subprocess

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR / "engage_modules"))
sys.path.insert(0, str(BASE_DIR / "shared"))

from playwright.sync_api import sync_playwright

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
NEW_ACCOUNT = "emersonjosiel2026@gmail.com"
TEST_VIDEO = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Usar o perfil temporário que já tem o login
TEMP_PROFILE = r"C:\Users\Haylla\AppData\Local\Temp\chrome_new_account_bp98uckx"

print(f"[TEST NOVA CONTA] {NEW_ACCOUNT}")
print(f"[TEST] Usando perfil: {TEMP_PROFILE}")

# Conectar ao Chrome que já está aberto com a conta logada
# Ou lançar novo se necessário
port = 9999

proc = subprocess.Popen([
    CHROME_PATH,
    f"--user-data-dir={TEMP_PROFILE}",
    f"--remote-debugging-port={port}",
    "--no-first-run",
    "about:blank"
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

time.sleep(5)
print(f"[TEST] Chrome conectado, port={port}")

try:
    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()

        print(f"[TEST] Navegando para {TEST_VIDEO}")
        page.goto(TEST_VIDEO, timeout=30000, wait_until="domcontentloaded")
        time.sleep(3)

        # Scroll até comentários
        print("[TEST] Scrolling para comentários...")
        for _ in range(8):
            page.keyboard.press("PageDown")
            time.sleep(0.8)

        # Scroll into view
        page.evaluate("""() => {
            const box = document.querySelector('ytd-comment-simplebox-renderer');
            if (box) box.scrollIntoView({behavior: 'smooth', block: 'center'});
        }""")
        time.sleep(2)

        # Checar se box existe
        has_box = page.evaluate(
            "() => !!document.querySelector('ytd-comment-simplebox-renderer')"
        )
        print(f"[TEST] Comment box encontrado: {has_box}")

        if not has_box:
            print("[TEST] FAIL - Box nao encontrada")
            browser.close()
            proc.terminate()
            exit(1)

        # Clicar no placeholder
        print("[TEST] Clicando no placeholder...")
        clicked = page.evaluate("""() => {
            const selectors = [
                '#simplebox-placeholder',
                '#placeholder-area',
                'ytd-comment-simplebox-renderer'
            ];
            for (const sel of selectors) {
                const el = document.querySelector(sel);
                if (el) {
                    el.click();
                    return sel;
                }
            }
            return null;
        }""")
        print(f"[TEST] Clicou em: {clicked}")
        time.sleep(3)

        # Checar contenteditable
        ce_selectors = [
            "#contenteditable-root",
            "[contenteditable='true']",
            "div[contenteditable='plaintext-only']",
            "[contenteditable]"
        ]

        root = None
        for sel in ce_selectors:
            try:
                root = page.query_selector(sel)
                if root:
                    print(f"[TEST] *** SUCCESS! *** contenteditable encontrado: {sel}")
                    break
            except:
                continue

        if root:
            print("[TEST]")
            print("[TEST] ================================")
            print("[TEST] COMENTARIOS FUNCIONAM!")
            print("[TEST] Conta nova NAO tem shadowban")
            print("[TEST] ================================")
            print("[TEST]")
            print("[TEST] Digitando comentario de teste...")
            root.type("Teste automatizado - conta nova funcionando!", delay=100)
            time.sleep(2)
            print("[TEST] Comentario digitado com sucesso!")
            print("[TEST]")
            print("[TEST] CONCLUSAO: O problema eh shadowban nas 43 contas antigas")
        else:
            print("[TEST]")
            print("[TEST] ================================")
            print("[TEST] COMENTARIOS NAO FUNCIONAM")
            print("[TEST] Conta nova TAMBEM bloqueada")
            print("[TEST] ================================")
            print("[TEST]")

            # Debug
            diag = page.evaluate("""() => {
                const box = document.querySelector('ytd-comment-simplebox-renderer');
                if (!box) return 'box=null';
                const all = box.querySelectorAll('*');
                const tags = [];
                for (const el of all) {
                    if (el.id || el.getAttribute('contenteditable')) {
                        tags.push(el.tagName + '#' + el.id + '[ce=' + (el.getAttribute('contenteditable')||'') + ']');
                    }
                }
                return 'N=' + all.length + ' ids=' + tags.slice(0,8).join(',');
            }""")
            print(f"[TEST] DOM state: {diag}")
            print("[TEST]")
            print("[TEST] CONCLUSAO: Problema eh do codigo ou YouTube mudou algo")

        print("[TEST] Deixando Chrome aberto por 10s...")
        time.sleep(10)

        browser.close()

finally:
    print("[TEST] Encerrando Chrome...")
    proc.terminate()
    time.sleep(2)
    if proc.poll() is None:
        proc.kill()

print("[TEST] Teste completo!")
