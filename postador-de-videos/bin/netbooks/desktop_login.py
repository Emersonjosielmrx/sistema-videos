"""desktop_login.py — roda no PC1: login das contas no DESKTOP (Windows, ssh "desktop"), igual aos notebooks.
O Chrome do perfil separado (C:\\postador-worker\\perfis\\<perfil>) abre na tela da dona por uma tarefa do Windows
(C:\\postador-worker\\abrir_cdp.ps1); daqui só digitamos o E-MAIL (dona, 23/10/2026). Senha/captcha = a dona.

    python bin\\netbooks\\desktop_login.py conferir <perfil>        # Studio abre logado? depois fecha (grava o login)
    python bin\\netbooks\\desktop_login.py abrir <perfil> <email>   # fecha o que estiver aberto, abre e digita o e-mail
"""
import json
import socket
import subprocess
import sys
import time
import urllib.request
from contextlib import contextmanager
from pathlib import Path

SSH = r"C:\Program Files\Git\usr\bin\ssh.exe"
PORTA = 9460
LOGINS = Path(__file__).resolve().parent.parent.parent / "config" / "netbooks_logins.json"


def _ssh(cmd, timeout=90):
    r = subprocess.run([SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "desktop", cmd], capture_output=True,
                       timeout=timeout)
    return ((r.stdout or b"") + (r.stderr or b"")).decode("utf-8", "replace")


@contextmanager
def tunel():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        porta = s.getsockname()[1]
    t = subprocess.Popen([SSH, "-o", "BatchMode=yes", "-o", "ExitOnForwardFailure=yes", "-N", "-L",
                          f"{porta}:127.0.0.1:{PORTA}", "desktop"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(30):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{porta}/json/version", timeout=3)
                break
            except Exception:  # noqa: BLE001
                time.sleep(0.5)
        else:
            raise RuntimeError("Chrome do desktop não responde na porta de controle")
        yield porta
    finally:
        t.terminate()


def _aberto():
    try:
        with tunel():
            return True
    except RuntimeError:
        return False


def fechar():
    """Fecha pelo próprio Chrome (Browser.close): fechamento normal grava os cookies — matar perde o login novo."""
    if not _aberto():
        return
    from playwright.sync_api import sync_playwright
    with tunel() as porta, sync_playwright() as p:
        br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        try:
            br.new_browser_cdp_session().send("Browser.close")
        except Exception:  # noqa: BLE001
            pass
    time.sleep(4)


def conferir(perfil):
    from playwright.sync_api import sync_playwright
    res = {}
    if not _aberto():  # a dona fechou a janela: abre o perfil de novo (página em branco) só pra conferir
        _ssh(f"powershell -NoProfile -ExecutionPolicy Bypass -File C:\\postador-worker\\abrir_cdp.ps1 -perfil {perfil} "
             "-url about:blank")
    with tunel() as porta, sync_playwright() as p:
        br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        pg = br.contexts[0].new_page()
        pg.goto("https://studio.youtube.com", timeout=120000)
        pg.wait_for_timeout(8000)
        res["youtube"] = "accounts.google.com" not in pg.url
        res["url"] = pg.url[:80]
        pg.close()
    dados = {}
    for _ in range(20):  # 28/10: falha de leitura virava {} e a gravação abaixo apagava os logins das outras máquinas
        try:
            dados = json.loads(LOGINS.read_text(encoding="utf-8"))
            break
        except FileNotFoundError:
            break
        except (OSError, ValueError):
            time.sleep(0.25)
    else:
        raise RuntimeError("netbooks_logins.json não lê — não gravo por cima")
    dados.setdefault(perfil, {})["desktop"] = {"youtube": res["youtube"], "em": time.strftime("%Y-%m-%dT%H:%M")}
    LOGINS.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"desktop {perfil}: {'LOGADO' if res['youtube'] else 'NÃO logado'} ({res['url']})")
    fechar()
    return res["youtube"]


def abrir(perfil, email):
    fechar()
    saida = _ssh(f"powershell -NoProfile -ExecutionPolicy Bypass -File C:\\postador-worker\\abrir_cdp.ps1 -perfil {perfil}")
    if "PRONTO" not in saida:
        raise RuntimeError("Chrome não abriu no desktop: " + " ".join(saida.split())[-160:])
    from playwright.sync_api import sync_playwright
    with tunel() as porta, sync_playwright() as p:
        br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        pg = next((x for x in br.contexts[0].pages if "google" in x.url), None) or br.contexts[0].pages[0]
        pg.bring_to_front()
        campo = pg.locator("input[type=email], #identifierId").first
        campo.wait_for(state="visible", timeout=60000)
        campo.click()
        campo.fill("")
        pg.keyboard.type(email, delay=60)
        pg.wait_for_timeout(500)
        pg.keyboard.press("Enter")
        pg.wait_for_timeout(5000)
        print(f"desktop {perfil}: e-mail digitado; agora em {pg.url[:80]}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:]
    if a[:1] == ["conferir"]:
        conferir(a[1].lower())
    elif a[:1] == ["abrir"]:
        abrir(a[1].lower(), a[2])
    else:
        print(__doc__)
