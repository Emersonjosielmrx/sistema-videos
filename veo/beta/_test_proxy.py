#!/usr/bin/env python3
"""Teste rapido: Chrome com proxy -> Flow -> verifica reCAPTCHA."""
import sys, os, time, subprocess, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright

PROXY_RAW = "<USUARIO>:<SEGREDO_REMOVIDO>@45.39.15.202:6632"
cred, hp = PROXY_RAW.rsplit("@", 1)
PROXY_USER, PROXY_PASS = cred.split(":", 1)
PROXY_HOST = hp

PORT = 9250
SESSION = "seebotsia"
PROFILE = "chrome_gen_seebotsia"

def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

# 1) Mata Chrome restante nessa porta
import urllib.request
try:
    urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version", timeout=2)
    log("Chrome ja rodando — vou usar")
    chrome_running = True
except:
    chrome_running = False

if not chrome_running:
    profile_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), PROFILE)
    os.makedirs(profile_path, exist_ok=True)
    chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    args = [
        chrome,
        f"--remote-debugging-port={PORT}",
        "--no-first-run",
        "--disable-session-crashed-bubble",
        "--disable-gpu",
        "--disable-software-rasterizer",
        "--disable-blink-features=AutomationControlled",
        "--disable-features=IsolateOrigins,site-per-process",
        "--disable-web-security",
        f"--user-data-dir={profile_path}",
        f"--proxy-server=http://{PROXY_HOST}",
        "about:blank",
    ]
    log(f"Lancando Chrome com proxy {PROXY_HOST}...")
    subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for i in range(20):
        time.sleep(1)
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version", timeout=2)
            log("Chrome aberto com sucesso!")
            chrome_running = True
            break
        except:
            pass
    if not chrome_running:
        log("FALHA ao abrir Chrome!")
        sys.exit(1)

# 2) Conectar Playwright + CDP auth
log("Conectando Playwright via CDP...")
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{PORT}")
    ctx = b.contexts[0]
    ctx.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        delete navigator.__proto__.webdriver;
    """)

    page = ctx.pages[0] if ctx.pages else ctx.new_page()

    # CDP Fetch auth pro proxy
    try:
        cdp = ctx.new_cdp_session(page)
        cdp.send("Fetch.enable", {"handleAuthRequests": True})
        def _on_auth(params):
            log(f"[proxy-auth] respondendo challenge...")
            cdp.send("Fetch.continueWithAuth", {
                "requestId": params["requestId"],
                "authChallengeResponse": {
                    "response": "ProvideCredentials",
                    "username": PROXY_USER,
                    "password": PROXY_PASS,
                }
            })
        def _on_paused(params):
            cdp.send("Fetch.continueRequest", {"requestId": params["requestId"]})
        cdp.on("Fetch.authRequired", _on_auth)
        cdp.on("Fetch.requestPaused", _on_paused)
        log(f"CDP Fetch auth configurado: {PROXY_USER}@{PROXY_HOST}")
    except Exception as e:
        log(f"AVISO: falha CDP auth: {e}")

    # 3) Testar IP
    log("Verificando IP visivel...")
    try:
        page.goto("https://api.ipify.org?format=json", timeout=15000)
        ip_text = page.text_content("body")
        log(f"IP visivel: {ip_text}")
    except Exception as e:
        log(f"Falha verificando IP: {e}")

    # 4) Navegar pro Flow
    log("Navegando pro Flow...")
    try:
        page.goto("https://labs.google/fx/pt/tools/flow", timeout=30000, wait_until="domcontentloaded")
        time.sleep(5)

        # Checar reCAPTCHA
        has_recaptcha = page.evaluate("""() => {
            const frames = Array.from(document.querySelectorAll('iframe'));
            return frames.some(f => (f.src || '').includes('recaptcha'));
        }""")

        if has_recaptcha:
            log("!!! reCAPTCHA DETECTADO mesmo com proxy !!!")
        else:
            log("SEM reCAPTCHA! Proxy funcionou!")

        # Checar se a pagina carregou
        title = page.title()
        log(f"Titulo da pagina: {title}")
        url_final = page.url
        log(f"URL final: {url_final}")

    except Exception as e:
        log(f"Erro navegando: {e}")

    log("Teste finalizado.")
