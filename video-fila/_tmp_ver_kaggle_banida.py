"""10/11 dona: 'inovaremanhwaverseita essa kaggle foi banida — verifique se as outras também'.
UMA conta por execução, pelo proxy fixo dela (ponte local). Entra com 'Sign in with Google' (o Google já logado no
cofre) e tira print da tela do Kaggle, sem gerar token nem clicar em mais nada."""
import re, socket, subprocess, sys, time, urllib.request
from pathlib import Path
sys.path.insert(0, r"D:\logins-google")
import cofre  # noqa: E402
email, saida = sys.argv[1], sys.argv[2]
COLAB = Path(r"D:\recapd-ambientes\producao\colab")
OUT = Path(r"D:\video-fila\_tmp_kaggle_print"); OUT.mkdir(exist_ok=True)
gratis = saida.startswith("ws-")
n = int(saida[3:] if gratis else saida)
porta_ponte = (18500 if gratis else 18300) + n
try:
    socket.create_connection(("127.0.0.1", porta_ponte), timeout=2).close()
except OSError:
    script = r"D:\video-fila\_tmp_ponte_ws.py" if gratis else str(COLAB / "ponte_proxy_fixo.py")
    subprocess.Popen([sys.executable, script, str(n), str(porta_ponte)], creationflags=0x08000000)
    time.sleep(40 if gratis else 5)
op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": f"http://127.0.0.1:{porta_ponte}",
                                                               "https": f"http://127.0.0.1:{porta_ponte}"}))
ip = None
for _ in range(3):
    try:
        ip = op.open("http://api.ipify.org", timeout=40).read().decode().strip(); break
    except Exception:
        time.sleep(5)
if not ip:
    sys.exit("a ponte do proxy não respondeu — parei antes de abrir a conta")
_em, e = cofre.conta(email)
if cofre._cdp_vivo(e["porta"]) or cofre.porta_aberta(Path(e["pasta"])):
    sys.exit("o Chrome da conta já está aberto sem o proxy — parei")
extra = [f"--proxy-server=http://127.0.0.1:{porta_ponte}", "--proxy-bypass-list=<-loopback>",
         "--force-webrtc-ip-handling-policy=disable_non_proxied_udp"]
porta, proc = cofre.abrir(email, "about:blank", visivel=False, extra=extra)
from playwright.sync_api import sync_playwright
nome = email.split("@")[0]
try:
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        pg = br.contexts[0].new_page()
        pg.goto("https://api.ipify.org", timeout=90000)
        ipc = pg.inner_text("body").strip()
        print("IP proxy", ip, "| IP Chrome", ipc, flush=True)
        if ipc != ip:
            raise SystemExit("o Chrome não saiu pelo proxy — parei antes do Kaggle")
        pg.goto("https://www.kaggle.com/settings", timeout=120000, wait_until="commit")
        pg.wait_for_timeout(12000)
        if "login" in pg.url:
            pg.get_by_text(re.compile(r"Sign in with Google", re.I)).first.click(timeout=30000)
            pg.wait_for_timeout(8000)
            for outra in br.contexts[0].pages:
                if "accounts.google" in outra.url:
                    try:
                        outra.get_by_text(email, exact=False).first.click(timeout=20000)
                        outra.wait_for_timeout(6000)
                        b = outra.get_by_role("button", name=re.compile(r"^(Continue|Continuar)$", re.I))
                        if b.count():
                            b.first.click()
                    except Exception:
                        pass
            pg.wait_for_timeout(15000)
        for alvo in br.contexts[0].pages:
            if "kaggle.com" in alvo.url:
                pg = alvo
        pg.screenshot(path=str(OUT / f"{nome}_kaggle.png"))
        print("URL:", pg.url, flush=True)
        print("TELA:", " ".join(pg.inner_text("body").split())[:600], flush=True)
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
