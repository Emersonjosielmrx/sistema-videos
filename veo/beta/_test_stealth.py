#!/usr/bin/env python3
"""Teste stealth anti-reCAPTCHA (sem proxy).
Abre Chrome com flags anti-detecção, aplica patches JS, limpa artefatos
reCAPTCHA e tenta carregar o Flow. Reporta se reCAPTCHA aparece.
"""
import subprocess, time, sys, os
from playwright.sync_api import sync_playwright

SESSAO = "emersonjosiel2027"
PORT = 9410
PROFILE = os.path.join(os.path.dirname(__file__), "profiles", "chrome_gen_nova_1786128033")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROJ = "https://labs.google/fx/pt/tools/flow"

def main():
    print(f"[1] Abrindo Chrome na porta {PORT} (perfil {SESSAO})...")
    chrome_args = [
        CHROME,
        f"--remote-debugging-port={PORT}",
        "--no-first-run",
        "--disable-session-crashed-bubble",
        "--disable-gpu",
        "--disable-software-rasterizer",
        "--disable-blink-features=AutomationControlled",
        "--disable-features=IsolateOrigins,site-per-process",
        "--disable-web-security",
        f"--user-data-dir={PROFILE}",
        "about:blank",
    ]
    proc = subprocess.Popen(chrome_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(5)

    print("[2] Conectando via CDP...")
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{PORT}")
        ctx = b.contexts[0]

        # Stealth patches (mesmo bloco do gera_auto.py)
        ctx.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            delete navigator.__proto__.webdriver;
            window.chrome = window.chrome || {};
            window.chrome.runtime = window.chrome.runtime || {
                PlatformOs: {MAC: 'mac', WIN: 'win', ANDROID: 'android', CROS: 'cros', LINUX: 'linux', OPENBSD: 'openbsd'},
                PlatformArch: {ARM: 'arm', X86_32: 'x86-32', X86_64: 'x86-64', MIPS: 'mips', MIPS64: 'mips64'},
                PlatformNaclArch: {ARM: 'arm', X86_32: 'x86-32', X86_64: 'x86-64', MIPS: 'mips', MIPS64: 'mips64'},
                RequestUpdateCheckStatus: {THROTTLED: 'throttled', NO_UPDATE: 'no_update', UPDATE_AVAILABLE: 'update_available'},
                OnInstalledReason: {INSTALL: 'install', UPDATE: 'update', CHROME_UPDATE: 'chrome_update', SHARED_MODULE_UPDATE: 'shared_module_update'},
                OnRestartRequiredReason: {APP_UPDATE: 'app_update', OS_UPDATE: 'os_update', PERIODIC: 'periodic'},
            };
            if (!window.chrome.csi) { window.chrome.csi = function() { return {startE: Date.now(), onloadT: Date.now(), pageT: Math.random()*1000+500, tran: 15}; }; }
            if (!window.chrome.loadTimes) { window.chrome.loadTimes = function() { return {commitLoadTime: Date.now()/1000, connectionInfo: 'h2', finishDocumentLoadTime: Date.now()/1000+0.1, finishLoadTime: Date.now()/1000+0.2, firstPaintAfterLoadTime: 0, firstPaintTime: Date.now()/1000+0.05, navigationType: 'Other', npnNegotiatedProtocol: 'h2', requestTime: Date.now()/1000-0.5, startLoadTime: Date.now()/1000-0.5, wasAlternateProtocolAvailable: false, wasFetchedViaSpdy: true, wasNpnNegotiated: true}; }; }
            const origQuery = window.Permissions.prototype.query;
            window.Permissions.prototype.query = function(params) {
                if (params && params.name === 'notifications') {
                    return Promise.resolve({state: Notification.permission});
                }
                return origQuery.call(this, params);
            };
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    const p = [
                        {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format'},
                        {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: ''},
                        {name: 'Native Client', filename: 'internal-nacl-plugin', description: ''}
                    ];
                    p.length = 3;
                    return p;
                }
            });
            Object.defineProperty(navigator, 'languages', {get: () => ['pt-BR', 'pt', 'en-US', 'en']});
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(param) {
                if (param === 37445) return 'Intel Inc.';
                if (param === 37446) return 'Intel Iris OpenGL Engine';
                return getParameter.call(this, param);
            };
        """)

        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        # Limpar artefatos reCAPTCHA
        print("[3] Limpando artefatos reCAPTCHA...")
        try:
            page.evaluate("""() => {
                const keys = Object.keys(localStorage);
                let removed = 0;
                keys.forEach(k => {
                    if (k.startsWith('_grecaptcha') || k.startsWith('rc::')) {
                        localStorage.removeItem(k);
                        removed++;
                    }
                });
                const skeys = Object.keys(sessionStorage);
                skeys.forEach(k => {
                    if (k.startsWith('_grecaptcha') || k.startsWith('rc::')) {
                        sessionStorage.removeItem(k);
                        removed++;
                    }
                });
                return removed;
            }""")
        except Exception as e:
            print(f"  (limpeza localStorage falhou: {e})")

        # Limpar cookies reCAPTCHA via CDP
        try:
            cdp = ctx.new_cdp_session(page)
            cookies = cdp.send("Network.getAllCookies").get("cookies", [])
            rc = [c for c in cookies if "recaptcha" in c.get("name","").lower() or "grecaptcha" in c.get("name","").lower() or "recaptcha" in c.get("domain","").lower()]
            for c in rc:
                cdp.send("Network.deleteCookies", {"name": c["name"], "domain": c.get("domain","")})
            print(f"  Cookies reCAPTCHA removidos: {len(rc)}")
            cdp.detach()
        except Exception as e:
            print(f"  (limpeza cookies falhou: {e})")

        # Limpar CacheStorage
        try:
            cdp2 = ctx.new_cdp_session(page)
            caches = cdp2.send("CacheStorage.requestCacheNames", {"securityOrigin": "https://labs.google"}).get("caches", [])
            for c in caches:
                cdp2.send("CacheStorage.deleteCache", {"cacheId": c["cacheId"]})
            print(f"  CacheStorage entries removidos: {len(caches)}")
            cdp2.detach()
        except Exception as e:
            print(f"  (limpeza CacheStorage falhou: {e})")

        # Verificar webdriver ANTES de ir pro Flow
        print("[4] Verificando stealth pre-goto...")
        wd = page.evaluate("() => navigator.webdriver")
        print(f"  navigator.webdriver = {wd}")
        cr = page.evaluate("() => typeof window.chrome.csi")
        print(f"  chrome.csi = {cr}")
        lt = page.evaluate("() => typeof window.chrome.loadTimes")
        print(f"  chrome.loadTimes = {lt}")

        # Navegar pro Flow
        print(f"[5] Navegando pra {PROJ}...")
        page.goto(PROJ, wait_until="domcontentloaded")
        page.wait_for_timeout(10000)

        # Verificar reCAPTCHA
        print("[6] Verificando reCAPTCHA...")
        has_rc = page.evaluate("""() => {
            const frames = Array.from(document.querySelectorAll('iframe'));
            return frames.some(f => (f.src || '').includes('recaptcha/enterprise'));
        }""")

        if has_rc:
            print("!!! reCAPTCHA DETECTADO — stealth NAO foi suficiente !!!")
            # Tentar reload
            print("[7] Tentando reload...")
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(8000)
            still = page.evaluate("""() => {
                const frames = Array.from(document.querySelectorAll('iframe'));
                return frames.some(f => (f.src || '').includes('recaptcha/enterprise'));
            }""")
            if still:
                print("!!! reCAPTCHA PERSISTIU apos reload !!!")
            else:
                print(">>> reCAPTCHA LIMPO apos reload! <<<")
        else:
            print(">>> SEM reCAPTCHA! Stealth funcionou! <<<")

        # Verificar se temos o textarea do prompt (sinal de que o Flow carregou OK)
        has_textarea = page.evaluate("""() => {
            const ta = document.querySelector('textarea');
            return !!ta;
        }""")
        print(f"  textarea do prompt encontrado: {has_textarea}")

        # URL final
        print(f"  URL final: {page.url}")
        print(f"  Title: {page.title()}")

        b.close()

    proc.terminate()
    print("\n[DONE]")

if __name__ == "__main__":
    main()
