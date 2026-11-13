"""
Debug comentários - garantir box visível e tentar diferentes triggers
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

print("[TEST] Garantindo box visivel na viewport")

profile_dir = get_profile_dir(TEST_ACCOUNT)
port = PORT_MAP.get(TEST_ACCOUNT, 9222)

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

try:
    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()

        page.goto(TEST_VIDEO, timeout=30000, wait_until="domcontentloaded")
        time.sleep(3)

        # Scroll até comentários aparecerem
        print("[TEST] Scrolling ate comentarios...")
        for _ in range(8):
            page.keyboard.press("PageDown")
            time.sleep(0.8)

        # Garantir que a box está na viewport
        print("[TEST] ScrollIntoView na box...")
        page.evaluate("""() => {
            const box = document.querySelector('ytd-comment-simplebox-renderer');
            if (box) {
                box.scrollIntoView({behavior: 'smooth', block: 'center'});
            }
        }""")
        time.sleep(2)

        # Verificar posição
        pos = page.evaluate("""() => {
            const box = document.querySelector('ytd-comment-simplebox-renderer');
            if (!box) return null;
            const rect = box.getBoundingClientRect();
            return {
                x: rect.left,
                y: rect.top,
                width: rect.width,
                height: rect.height,
                inViewport: rect.top >= 0 && rect.top <= window.innerHeight
            };
        }""")
        print(f"[TEST] Box position: {pos}")

        if not pos or not pos['inViewport']:
            print("[TEST] ERRO - Box nao esta na viewport")
            browser.close()
            proc.terminate()
            exit(1)

        # Tentar ativar - método 1: click no centro da box
        print("[TEST] Click no centro da box...")
        click_x = pos['x'] + pos['width'] / 2
        click_y = pos['y'] + 30  # Um pouco abaixo do topo

        page.mouse.click(click_x, click_y)
        time.sleep(2)

        # Checar contenteditable
        ce = page.query_selector("#contenteditable-root, [contenteditable]")
        if ce:
            print("[TEST] SUCCESS - contenteditable encontrado apos click!")
            ce.type("Teste funciona!", delay=100)
            print("[TEST] Comentario digitado")
        else:
            print("[TEST] FAIL - contenteditable nao apareceu")

            # Tentar forçar ativação via JS
            print("[TEST] Tentando forcar ativacao via JS...")
            activated = page.evaluate("""() => {
                const box = document.querySelector('ytd-comment-simplebox-renderer');
                if (!box) return false;

                // Tentar disparar eventos Polymer
                box.dispatchEvent(new Event('focus', {bubbles: true}));
                box.dispatchEvent(new Event('click', {bubbles: true}));
                box.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                box.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));

                // Tentar clicar no placeholder
                const ph = box.querySelector('#simplebox-placeholder');
                if (ph) {
                    ph.dispatchEvent(new Event('click', {bubbles: true}));
                    ph.dispatchEvent(new Event('tap', {bubbles: true, composed: true}));
                }

                return true;
            }""")
            time.sleep(2)

            ce = page.query_selector("#contenteditable-root, [contenteditable]")
            if ce:
                print("[TEST] SUCCESS via JS forçado!")
                ce.type("Teste via JS", delay=100)
            else:
                print("[TEST] FAIL - JS forcado tambem nao funcionou")

                # Debug: verificar se há erros no console
                print("[TEST] Capturando logs do console...")
                logs = []

                def handle_console(msg):
                    logs.append(f"{msg.type}: {msg.text}")

                page.on("console", handle_console)

                # Tentar mais uma vez e capturar logs
                page.evaluate("document.querySelector('#simplebox-placeholder')?.click()")
                time.sleep(1)

                if logs:
                    print(f"[TEST] Console logs: {logs[:5]}")

        browser.close()

finally:
    proc.terminate()
    time.sleep(1)
    if proc.poll() is None:
        proc.kill()

print("[TEST] Fim")
