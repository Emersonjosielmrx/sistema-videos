r"""
rclone no Google Drive de uma conta do cofre: autoriza pelo Chrome do cofre (sem digitar senha) e cria o remoto.

  python rclone_drive_conta.py <conta> <remoto>        ex.: emersonjosiel649 colab649

Passos: `rclone authorize drive` abre o servidor local 53682 -> a URL vai pro Chrome do cofre -> seletor de conta
(clica o e-mail) -> consentimento "Continuar" -> rclone recebe o token -> `rclone config create <remoto> drive`.
Config fica no rclone.conf padrão (o mesmo do manhwa-drive:). 24/10: colab649 criado assim (Drive com 3 GB livres).
"""
import json
import re
import subprocess
import sys
import threading
import time

sys.path.insert(0, r"D:\logins-google")
import cofre
from playwright.sync_api import sync_playwright

RCLONE = r"D:\tools\rclone.exe"


def autorizar(conta, remoto):
    email = cofre.conta(conta)[0]
    proc = subprocess.Popen([RCLONE, "authorize", "drive", "--auth-no-open-browser"], stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True)
    saida = []
    threading.Thread(target=lambda: [saida.append(l) for l in proc.stdout], daemon=True).start()

    url = None
    fim = time.time() + 30
    while time.time() < fim and not url:
        m = re.search(r"http://127\.0\.0\.1:53682/auth\?state=\S+", "".join(saida))
        url = m.group(0) if m else None
        time.sleep(0.5)
    if not url:
        proc.kill()
        raise SystemExit("rclone nao deu a URL: " + "".join(saida)[-500:])

    porta, chrome = cofre.abrir(conta, url="about:blank", visivel=True)
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        page = br.contexts[0].new_page()
        page.goto(url, timeout=60000)
        fim = time.time() + 180
        while time.time() < fim and proc.poll() is None:
            page.wait_for_timeout(2500)
            try:
                if "accountchooser" in page.url or "selectaccount" in page.url.lower():
                    e = page.get_by_text(email, exact=True)
                    if e.count() and e.first.is_visible():
                        e.first.click()
                    continue
                for txt in ("Continuar", "Continue", "Permitir", "Allow"):
                    b = page.get_by_role("button", name=txt, exact=True)
                    if b.count() and b.first.is_visible():
                        b.first.click()
                        break
            except Exception:
                pass
        page.close()
        cofre.fechar(chrome, br, nome=conta)

    time.sleep(2)
    m = re.search(r"\{\"access_token\"[^\n]*\}", "".join(saida))
    if not m:
        raise SystemExit("token nao veio: " + "".join(saida)[-800:])
    token = m.group(0)
    json.loads(token)
    subprocess.run([RCLONE, "config", "create", remoto, "drive", "scope", "drive", "token", token], check=True,
                   capture_output=True)
    r = subprocess.run([RCLONE, "about", f"{remoto}:", "--timeout", "60s"], capture_output=True, text=True)
    print(r.stdout or r.stderr[-300:])


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
    else:
        autorizar(sys.argv[1], sys.argv[2])
