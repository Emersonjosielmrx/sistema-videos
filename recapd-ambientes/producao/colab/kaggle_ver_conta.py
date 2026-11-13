"""kaggle_ver_conta.py — OLHA o estado de UMA conta do Kaggle pelo IP fixo dela (09/11/2026). Não gera token, não grava
no pool, não clica em nada além de abrir a página. Uma conta por execução; NUNCA em laço (INCIDENTE_BANIMENTO_02NOV.md).

Motivo: 10 contas passaram a dar "authentication required" juntas às 14:44 de 09/11 com o proxy respondendo 200.
Antes de gerar token novo (dona 09/11: "gere"), ver se a conta foi suspensa/banida ou só o token caiu.

    python kaggle_ver_conta.py <username do pool>
Saída: _kaggle/ver_<username>/settings.png + texto do estado no terminal.
"""
import json
import socket
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
import cofre  # noqa: E402
from kaggle_token_proxy import ip_pela_ponte  # noqa: E402

AQUI = Path(__file__).resolve().parent


def main():
    user = sys.argv[1]
    pool = json.loads((AQUI / "kaggle_pool.json").read_text(encoding="utf-8"))
    c = next(x for x in pool["contas"] if x.get("username") == user)
    px = c.get("proxy_fixo") or ""
    if "rnprmtfo-" not in px:
        sys.exit(f"{user} não tem proxy_fixo rnprmtfo — não abro (sairia pelo IP errado)")
    n = int(px.split("rnprmtfo-", 1)[1].split(":", 1)[0])
    email = c["cofre"]
    _em, e = cofre.conta(email)
    if cofre._cdp_vivo(e["porta"]) or cofre.porta_aberta(Path(e["pasta"])):
        sys.exit(f"o Chrome de {email} já está aberto SEM o proxy — feche antes")
    porta_ponte = 18300 + n
    try:
        socket.create_connection(("127.0.0.1", porta_ponte), timeout=2).close()
    except OSError:
        subprocess.Popen([sys.executable, str(AQUI / "ponte_proxy_fixo.py"), str(n), str(porta_ponte)],
                         creationflags=0x08000000)
        time.sleep(3)
    ip = ip_pela_ponte(porta_ponte)
    print(f"{user}: saída rnprmtfo-{n} = {ip} (pool diz {c.get('ip_real')})", flush=True)
    extra = [f"--proxy-server=http://127.0.0.1:{porta_ponte}", "--proxy-bypass-list=<-loopback>",
             "--force-webrtc-ip-handling-policy=disable_non_proxied_udp"]
    porta, proc = cofre.abrir(email, "about:blank", visivel=False, extra=extra)
    if proc is None:
        sys.exit("o cofre devolveu uma janela já aberta (sem proxy) — parei")
    saida = AQUI / "_kaggle" / f"ver_{user}"
    saida.mkdir(parents=True, exist_ok=True)
    from playwright.sync_api import sync_playwright
    try:
        with sync_playwright() as p:
            br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
            pg = br.contexts[0].new_page()
            pg.goto("https://api.ipify.org", timeout=60000)
            ip_chrome = pg.inner_text("body").strip()
            if ip_chrome != ip:
                raise SystemExit(f"o Chrome NÃO saiu pelo proxy ({ip_chrome} != {ip}) — parei antes do Kaggle")
            pg.goto("https://www.kaggle.com/settings", timeout=120000, wait_until="commit")
            pg.wait_for_timeout(15000)
            if "login" in pg.url:  # entra com o Google do cofre (mesmo passo do kaggle_token_proxy), ainda pelo proxy
                import re
                try:  # aviso de cookies cobre o botão
                    pg.get_by_text(re.compile(r"^OK, Got it\.?$", re.I)).first.click(timeout=5000)
                except Exception:  # noqa: BLE001
                    pass
                pg.get_by_text(re.compile(r"Sign in with Google|Entrar com o Google", re.I)).first.click(timeout=30000,
                                                                                                          force=True)
                pg.wait_for_timeout(8000)
                for outra in br.contexts[0].pages:
                    if "accounts.google" in outra.url:
                        try:
                            outra.get_by_text(email, exact=False).first.click(timeout=20000)
                            outra.wait_for_timeout(6000)
                            b = outra.get_by_role("button", name=re.compile(r"^(Continue|Continuar|Allow|Permitir)$", re.I))
                            if b.count():
                                b.first.click()
                        except Exception:  # noqa: BLE001
                            pass
                pg.wait_for_timeout(12000)
                pg.goto("https://www.kaggle.com/settings", timeout=120000, wait_until="commit")
                pg.wait_for_timeout(12000)
            pg.screenshot(path=str(saida / "settings.png"), full_page=True)
            corpo = pg.inner_text("body")[:4000]
            (saida / "settings.txt").write_text(f"url: {pg.url}\n\n{corpo}", encoding="utf-8")
            low = corpo.lower()
            if "suspended" in low or "banned" in low:
                estado = "SUSPENSA/BANIDA"
            elif "login" in pg.url:
                estado = "DESLOGADA (precisa entrar com o Google)"
            elif "api" in low:
                estado = "LOGADA, conta ativa (a API caiu = token)"
            else:
                estado = "indefinido — ver print"
            print(f"{user}: {estado} | url {pg.url}", flush=True)
            try:
                br.new_browser_cdp_session().send("Browser.close")
            except Exception:  # noqa: BLE001
                pass
    finally:
        try:
            proc.wait(timeout=20)
        except Exception:  # noqa: BLE001
            proc.kill()
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Get-CimInstance Win32_Process -Filter \"name='chrome.exe'\" | Where-Object { $_.CommandLine "
                        "-match '" + Path(e["pasta"]).name + "' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"],
                       capture_output=True, creationflags=0x08000000)


if __name__ == "__main__":
    main()
