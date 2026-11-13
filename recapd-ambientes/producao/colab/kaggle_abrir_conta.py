"""kaggle_abrir_conta.py — abre NA TELA o Chrome de UMA conta do Kaggle, saindo SÓ pelo IP fixo dela (10/11/2026).
Dona 10/11: "abre na tela já com o proxy dela" (ver se foi suspensa ou se o Google pede confirmação).
Confere que o Chrome sai pelo proxy antes de ir ao Kaggle; a janela fica aberta pra dona (não fecha sozinha).
Uma conta por execução; nunca em laço (INCIDENTE_BANIMENTO_02NOV.md).

    python kaggle_abrir_conta.py <username do pool>
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
    print(f"{user} ({email}): saída rnprmtfo-{n} = {ip}", flush=True)
    extra = [f"--proxy-server=http://127.0.0.1:{porta_ponte}", "--proxy-bypass-list=<-loopback>",
             "--force-webrtc-ip-handling-policy=disable_non_proxied_udp"]
    porta, proc = cofre.abrir(email, "about:blank", visivel=True, extra=extra)
    if proc is None:
        sys.exit("o cofre devolveu uma janela já aberta (sem proxy) — parei")
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        pg = br.contexts[0].pages[0] if br.contexts[0].pages else br.contexts[0].new_page()
        pg.goto("https://api.ipify.org", timeout=60000)
        ip_chrome = pg.inner_text("body").strip()
        if ip_chrome != ip:
            proc.kill()
            raise SystemExit(f"o Chrome NÃO saiu pelo proxy ({ip_chrome} != {ip}) — fechei antes do Kaggle")
        print(f"Chrome conferido saindo por {ip_chrome}", flush=True)
        pg.goto("https://www.kaggle.com/settings", timeout=120000, wait_until="commit")
        print("janela aberta no Kaggle — a dona olha e fecha quando terminar", flush=True)


if __name__ == "__main__":
    main()
