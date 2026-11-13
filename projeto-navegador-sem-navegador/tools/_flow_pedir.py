"""Teste de captura: segura a trava da conta, liga a escuta CDP, manda 1 pedido pela caixa do Flow e espera."""
import sys, time, subprocess
from filelock import FileLock
from playwright.sync_api import sync_playwright
porta, pedido, espera, saida = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
trava = FileLock(rf"D:\veo\beta\logs\.cdp_lock_{porta}", timeout=30); trava.acquire()
cap = subprocess.Popen([sys.executable, "-u", r"D:\projeto-navegador-sem-navegador\tools\capturar_cdp.py", porta,
                        "--filtro", r"^(?!.*(gstatic|play\.google\.com/log|google-analytics|googletagmanager|fonts\.|/asb/|lh3\.)).*", "--saida", saida, "--segundos", str(espera + 15)])
time.sleep(5)
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
    pg = [x for c in b.contexts for x in c.pages if "flow" in x.url][0]
    pg.bring_to_front()
    pg.locator(".ProseMirror, [contenteditable=true]").last.focus()
    pg.wait_for_timeout(500); pg.keyboard.type(pedido, delay=5); pg.wait_for_timeout(800)
    pg.keyboard.press("Enter")
    print("enviado", flush=True)
    pg.wait_for_timeout(espera * 1000)
    pg.screenshot(path=r"D:\projeto-navegador-sem-navegador\capturas\telas\flow_depois.png", timeout=20000)
cap.wait(); trava.release()
