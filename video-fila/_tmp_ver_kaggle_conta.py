"""09/11 (dona: 'esses que não leem o token pode acessar a conta pelo navegador e ver se foram explodidos, usando o
proxy delas'). UMA conta, pelo proxy fixo dela (ponte local), só abre e tira print — não gera token nem clica nada."""
import socket, subprocess, sys, time, urllib.request
from pathlib import Path
sys.path.insert(0, r"D:\logins-google")
import cofre  # noqa: E402
email, n = sys.argv[1], int(sys.argv[2])
AQUI = Path(r"D:\recapd-ambientes\producao\colab")
porta_ponte = 18300 + n
try:
    socket.create_connection(("127.0.0.1", porta_ponte), timeout=2).close()
except OSError:
    subprocess.Popen([sys.executable, str(AQUI / "ponte_proxy_fixo.py"), str(n), str(porta_ponte)], creationflags=0x08000000)
    time.sleep(3)
op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": f"http://127.0.0.1:{porta_ponte}",
                                                               "https": f"http://127.0.0.1:{porta_ponte}"}))
ip = op.open("http://api.ipify.org", timeout=30).read().decode().strip()
_em, e = cofre.conta(email)
if cofre._cdp_vivo(e["porta"]) or cofre.porta_aberta(Path(e["pasta"])):
    sys.exit("Chrome da conta já aberto sem proxy — parei")
extra = [f"--proxy-server=http://127.0.0.1:{porta_ponte}", "--proxy-bypass-list=<-loopback>",
         "--force-webrtc-ip-handling-policy=disable_non_proxied_udp"]
porta, proc = cofre.abrir(email, "about:blank", visivel=False, extra=extra)
out = Path(r"D:\video-fila\_tmp_kaggle_print")
out.mkdir(exist_ok=True)
from playwright.sync_api import sync_playwright
try:
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        pg = br.contexts[0].new_page()
        pg.goto("https://api.ipify.org", timeout=60000)
        ipc = pg.inner_text("body").strip()
        print("IP proxy", ip, "| IP Chrome", ipc)
        if ipc != ip:
            raise SystemExit("Chrome não saiu pelo proxy — parei antes do Kaggle")
        import re
        pg.goto("https://www.kaggle.com/settings", timeout=120000, wait_until="commit")
        pg.wait_for_timeout(10000)
        if "login" in pg.url:
            pg.get_by_text(re.compile(r"Sign in with Google", re.I)).first.click(timeout=30000)
            pg.wait_for_timeout(8000)
            for outra in br.contexts[0].pages:
                if "accounts.google" in outra.url:
                    try:
                        outra.get_by_text(email, exact=False).first.click(timeout=20000)
                        outra.wait_for_timeout(6000)
                        b = outra.get_by_role("button", name=re.compile(r"^(Continue|Continuar|Allow|Permitir)$", re.I))
                        if b.count():
                            b.first.click()
                    except Exception:
                        pass
            pg.wait_for_timeout(12000)
        for nome, url in (("settings", "https://www.kaggle.com/settings"),
                          ("code", "https://www.kaggle.com/work/code")):
            pg.goto(url, timeout=120000, wait_until="commit")
            pg.wait_for_timeout(12000)
            pg.screenshot(path=str(out / f"{email.split('@')[0]}_{nome}.png"), full_page=False)
            t = pg.inner_text("body")
            print(nome, pg.url, "|", " ".join(t.split())[:300])
        try:
            br.new_browser_cdp_session().send("Browser.close")
        except Exception:
            pass
finally:
    if proc:
        try:
            proc.wait(timeout=20)
        except Exception:
            proc.kill()
