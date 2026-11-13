"""
Debug comentários - teste com interação mais natural
Hipótese: YouTube precisa de mais interação orgânica antes de ativar comentários
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
import subprocess

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
TEST_ACCOUNT = "aulacomia"
TEST_VIDEO = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

print("[DEBUG] Teste com interacao organica antes de comentar")
print(f"[DEBUG] Conta: {TEST_ACCOUNT}")

profile_dir = get_profile_dir(TEST_ACCOUNT)
port = PORT_MAP.get(TEST_ACCOUNT, 9222)

# Launch Chrome SEM headless pra ver o que acontece
proc = subprocess.Popen([
    CHROME_PATH,
    f"--user-data-dir={profile_dir}",
    f"--remote-debugging-port={port}",
    # "--headless=new",  # DESLIGADO pra debug visual
    "--no-first-run",
    "--disable-gpu",
    "--mute-audio",
    "about:blank"
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

time.sleep(5)
print(f"[DEBUG] Chrome aberto (visible mode), port={port}")

try:
    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()

        print(f"[DEBUG] Navegando pra {TEST_VIDEO}")
        page.goto(TEST_VIDEO, timeout=30000, wait_until="domcontentloaded")
        time.sleep(3)

        # Simular visualização orgânica
        print("[DEBUG] Simulando visualizacao organica...")

        # Assistir um pouco do vídeo
        print("[DEBUG] - Assistindo video por 5s")
        time.sleep(5)

        # Scroll suave pra baixo
        print("[DEBUG] - Scroll suave (5x)")
        for i in range(5):
            page.evaluate("window.scrollBy(0, 200)")
            time.sleep(random.uniform(0.8, 1.5))

        # Voltar pro topo, assistir mais um pouco
        print("[DEBUG] - Scroll de volta pro topo")
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(3)

        # Scroll pro meio (onde fica comentários)
        print("[DEBUG] - Scroll ate comentarios")
        for _ in range(3):
            page.keyboard.press("PageDown")
            time.sleep(random.uniform(0.8, 1.2))

        # Esperar comentários carregarem
        time.sleep(2)

        # Checar se box apareceu
        has_box = page.evaluate(
            "() => !!document.querySelector('ytd-comment-simplebox-renderer')"
        )
        print(f"[DEBUG] Comment box encontrado: {has_box}")

        if not has_box:
            print("[DEBUG] FAIL - Box de comentario nao carregou")
            browser.close()
            proc.terminate()
            exit(1)

        # Tentar ativar o campo
        print("[DEBUG] Tentando ativar campo de comentario...")

        # Método 1: Click direto no placeholder com mouse move realista
        print("[DEBUG] - Metodo 1: Mouse move + click")
        box_pos = page.evaluate("""() => {
            const box = document.querySelector('ytd-comment-simplebox-renderer');
            if (!box) return null;
            const rect = box.getBoundingClientRect();
            return {x: rect.left + rect.width/2, y: rect.top + 20};
        }""")

        if box_pos:
            # Move mouse gradualmente
            page.mouse.move(box_pos['x'], box_pos['y'], steps=10)
            time.sleep(0.5)
            page.mouse.click(box_pos['x'], box_pos['y'])
            print(f"[DEBUG] - Clicou em ({box_pos['x']}, {box_pos['y']})")
            time.sleep(3)

        # Checar se contenteditable apareceu
        ce = page.query_selector("#contenteditable-root, [contenteditable='true']")

        if ce:
            print("[DEBUG] SUCCESS! contenteditable ENCONTRADO")
            print("[DEBUG] Digitando comentario de teste...")
            ce.type("Teste automatizado - verificando funcionalidade", delay=120)
            time.sleep(2)
            print("[DEBUG] Comentario digitado (NAO submetendo)")
        else:
            print("[DEBUG] FAIL - contenteditable ainda nao apareceu")

            # Debug detalhado
            diag = page.evaluate("""() => {
                const box = document.querySelector('ytd-comment-simplebox-renderer');
                if (!box) return 'box=null';

                const info = {
                    display: window.getComputedStyle(box).display,
                    visibility: window.getComputedStyle(box).visibility,
                    innerHTML_len: box.innerHTML.length,
                    children: box.children.length
                };

                // Checar shadow DOM
                const shadowHosts = box.querySelectorAll('*');
                let hasShadow = false;
                for (const el of shadowHosts) {
                    if (el.shadowRoot) {
                        hasShadow = true;
                        break;
                    }
                }
                info.hasShadowDOM = hasShadow;

                // Listar IDs
                const ids = Array.from(box.querySelectorAll('[id]')).map(el => el.id);
                info.ids = ids.slice(0, 10);

                return JSON.stringify(info, null, 2);
            }""")

            print(f"[DEBUG] DOM state:\n{diag}")

            # Tentar método 2: Tab navigation
            print("[DEBUG] - Metodo 2: Tab navigation")
            page.keyboard.press("Tab")
            time.sleep(0.5)
            page.keyboard.press("Tab")
            time.sleep(1.5)

            ce = page.query_selector("#contenteditable-root, [contenteditable]")
            if ce:
                print("[DEBUG] SUCCESS via Tab! contenteditable encontrado")
                ce.type("Teste via Tab", delay=120)
            else:
                print("[DEBUG] FAIL - Tab tambem nao funcionou")

        print("\n[DEBUG] Deixando Chrome aberto por 30s pra inspecao manual...")
        print("[DEBUG] Inspecione visualmente se o campo de comentario esta ativo")
        time.sleep(30)

        browser.close()

finally:
    print("[DEBUG] Matando Chrome...")
    proc.terminate()
    time.sleep(2)
    if proc.poll() is None:
        proc.kill()

print("[DEBUG] Teste completo")
