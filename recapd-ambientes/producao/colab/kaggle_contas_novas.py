r"""kaggle_contas_novas.py — assistente de contas NOVAS do Kaggle (dona 10/11), uma por vez, sem precisar do chat.

Para cada "email:N" da lista:
  1. abre o Chrome da conta (cofre) VISÍVEL saindo SÓ pelo proxy pago fixo rnprmtfo-N (ponte_proxy_fixo.py),
     confere o IP (tem que ser o do proxy e NUNCA visto no pool — IP queimado para) e abre accounts.google.com +
     kaggle.com/account/login;
  2. a dona faz o login do Google (senha/SMS) e o cadastro no Kaggle (Register with Google) e FECHA a janela;
  3. o script roda kaggle_token_proxy.py <email> <N> (mesmo proxy, oculto): gera o token e põe a conta no pool
     (verificada=false até a dona confirmar o telefone no Kaggle) — e marca google=vivo no cofre;
  4. passa para a próxima.
Nunca 2 contas no mesmo IP: cada N é exclusivo, conferido antes. Log: logs\kaggle_contas_novas.log

    wscript D:\rodar_oculto.vbs python kaggle_contas_novas.py inovaremanhwaverse7@gmail.com:10 ...
"""
import json
import socket
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
import cofre  # noqa: E402

AQUI = Path(__file__).resolve().parent
POOL = AQUI / "kaggle_pool.json"
LOG = AQUI.parent / "logs" / "kaggle_contas_novas.log"
MAX_S = 45 * 60
SO_KAGGLE = "--so-kaggle" in sys.argv


def log(t):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {t}"
    print(linha, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def _ponte(n):
    porta = 18300 + n
    try:
        socket.create_connection(("127.0.0.1", porta), timeout=2).close()
    except OSError:
        subprocess.Popen([sys.executable, str(AQUI / "ponte_proxy_fixo.py"), str(n), str(porta)],
                         creationflags=0x08000000)
        for _ in range(20):  # 11/11: 3 s não bastava (verse9/2034: "conexão recusada") — espera a ponte escutar
            time.sleep(1)
            try:
                socket.create_connection(("127.0.0.1", porta), timeout=2).close()
                break
            except OSError:
                continue
    op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": f"http://127.0.0.1:{porta}",
                                                                   "https": f"http://127.0.0.1:{porta}"}))
    # 11/11: o Webshare às vezes leva 13 s ou dá 502 num pedido simples (alternando com 0,4 s) — tenta 3x antes de desistir
    for t in range(3):
        try:
            return porta, op.open("https://api.ipify.org", timeout=30).read().decode().strip()
        except Exception:  # noqa: BLE001
            if t == 2:
                raise
            time.sleep(3)


def _vivo(porta):
    """11/11: com a CPU do PC1 a 100% o /json/version passava de 3 s, 1 falha = "fechou" e a janela era morta 5 min
    depois de abrir ("45 min sem fechar"). Só é fechada após 3 falhas seguidas, cada uma com até 10 s."""
    for _ in range(3):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{porta}/json/version", timeout=10)
            return True
        except Exception:  # noqa: BLE001
            time.sleep(2)
    return False


def _esperar_fechar(email, porta, proc, e):
    """11/11: verse7 deu "45 min sem fechar" 24 s depois de abrir — a janela ainda abrindo parecia fechada. Só conta
    como fechada depois de ter sido vista aberta (até 60 s pra aparecer).
    Espera a dona fechar a janela (até MAX_S). Depois espera a pasta do perfil liberar — 11/11: verse8/verse9 o
    token parou com "Chrome aberto SEM o proxy" porque a pasta ainda estava presa pelo Chrome que fechava."""
    for _ in range(30):
        if _vivo(porta):
            break
        time.sleep(2)
    fim = time.time() + MAX_S
    while time.time() < fim and _vivo(porta):
        time.sleep(5)
    if _vivo(porta):
        log(f"{email}: 45 min sem fechar — fechei; fica para a próxima vez")
        try:
            proc.kill()
        except Exception:  # noqa: BLE001
            pass
        return False
    for _ in range(30):
        time.sleep(2)
        if not cofre._cdp_vivo(porta) and not cofre.porta_aberta(Path(e["pasta"])):
            break
    try:
        proc.wait(timeout=10)
    except Exception:  # noqa: BLE001
        pass
    return True


def uma(email, n):
    pool = json.loads(POOL.read_text("utf-8"))
    if any(c.get("cofre") == email for c in pool["contas"]):
        log(f"{email}: já está no pool — pulo")
        return
    usados = {c.get("proxy_fixo", "").split("://")[-1].split(":")[0] for c in pool["contas"]}
    if f"rnprmtfo-{n}" in usados:
        log(f"{email}: rnprmtfo-{n} já é de outra conta — PAREI esta")
        return
    _em, e = cofre.conta(email)
    if cofre._cdp_vivo(e["porta"]) or cofre.porta_aberta(Path(e["pasta"])):
        log(f"{email}: Chrome da conta já aberto (sem proxy) — PAREI esta")
        return
    porta_ponte, ip = _ponte(n)
    queimados = {c.get("ip_real") for c in pool["contas"] if c.get("ip_real")}
    if ip in queimados:
        log(f"{email}: IP {ip} do rnprmtfo-{n} já foi de outra conta (queimado) — PAREI esta")
        return
    extra = [f"--proxy-server=http://127.0.0.1:{porta_ponte}", "--proxy-bypass-list=<-loopback>",
             "--force-webrtc-ip-handling-policy=disable_non_proxied_udp"]
    porta, proc = cofre.abrir(email, "https://api.ipify.org", visivel=True, extra=extra)
    if proc is None:
        log(f"{email}: o cofre devolveu janela já aberta — PAREI esta")
        return
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        pg = br.contexts[0].pages[0]
        ip_chrome = ""
        for _t in range(3):  # 11/11: página de erro por lentidão do Webshare (verse9/verse7) — recarrega até 3x
            try:
                pg.wait_for_timeout(4000)
                ip_chrome = pg.inner_text("body", timeout=30000).strip()
                if ip_chrome == ip:
                    break
                pg.goto("https://api.ipify.org", timeout=60000)
            except Exception:  # noqa: BLE001
                try:
                    pg.goto("https://api.ipify.org", timeout=60000)
                except Exception:  # noqa: BLE001
                    pass
        if ip_chrome != ip:
            log(f"{email}: Chrome NÃO saiu pelo proxy ({ip_chrome} != {ip}) — fechando, PAREI esta")
            br.new_browser_cdp_session().send("Browser.close")
            return
        # 11/11 (dona: "é só abrir primeiro pra logar no Google normal, fora do Kaggle"): 1ª janela = SÓ o Google
        if not SO_KAGGLE:
            pg.goto("https://accounts.google.com/ServiceLogin?Email=" + email, timeout=90000, wait_until="commit")
        br.close()  # solta o CDP; a janela continua aberta para a dona
    if SO_KAGGLE:  # já logada no Google (ex. verse8): fecha esta e vai direto ao Kaggle
        try:
            proc.kill()
        except Exception:  # noqa: BLE001
            pass
    else:
        log(f"{email}: [1/2] GOOGLE aberto pelo rnprmtfo-{n} ({ip}) — dona: logar no Google e FECHAR a janela")
        if not _esperar_fechar(email, porta, proc, e):
            return
    # 2ª janela, mesmo proxy: o Kaggle (Register/Sign in with Google), já logada no Google
    # 11/11: verse8 "não abriu a porta em 45 s" — Chrome anterior ainda vivo segurando a pasta: fecha o que sobrou
    subprocess.run(["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_Process -Filter \"name='chrome.exe'\" | "
                    f"Where-Object {{ $_.CommandLine -match '{Path(e['pasta']).name}' }} | ForEach-Object {{ Stop-Process "
                    "-Id $_.ProcessId -Force }"], capture_output=True, creationflags=0x08000000)
    time.sleep(4)
    porta, proc = cofre.abrir(email, "https://www.kaggle.com/account/login", visivel=True, extra=extra)
    if proc is None:
        log(f"{email}: o cofre devolveu janela já aberta na etapa do Kaggle — PAREI esta")
        return
    log(f"{email}: [2/2] KAGGLE aberto pelo mesmo proxy — dona: 'Register with Google' (ou Sign in) e FECHAR")
    if not _esperar_fechar(email, porta, proc, e):
        return
    # 11/11: verse7 — 11 processos do Chrome ficaram vivos depois de fechar (filhos) e o token parou com "Chrome aberto
    # SEM o proxy": derruba a árvore toda do perfil antes do token
    subprocess.run(["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_Process -Filter \"name='chrome.exe'\" | "
                    f"Where-Object {{ $_.CommandLine -match '{Path(e['pasta']).name}' }} | ForEach-Object {{ taskkill /F /T "
                    "/PID $_.ProcessId 2>$null }"], capture_output=True, creationflags=0x08000000)
    time.sleep(4)
    log(f"{email}: janela fechada — gerando o token pelo mesmo proxy")
    r = subprocess.run([sys.executable, str(AQUI / "kaggle_token_proxy.py"), email, str(n)], capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=900, creationflags=0x08000000)
    saida = (r.stdout + r.stderr).strip().splitlines()
    log(f"{email}: token -> {(saida[-1] if saida else 'sem saída')[:200]}")
    if any(l.startswith("OK ") for l in saida):
        try:
            cofre._marcar(email, google="vivo", checado=datetime.now().isoformat(timespec="minutes"))
        except Exception:  # noqa: BLE001
            pass


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for item in [a for a in sys.argv[1:] if not a.startswith("--")]:
        email, _, n = item.rpartition(":")
        try:
            uma(email, int(n))
        except Exception as e:  # noqa: BLE001
            log(f"{email}: erro {type(e).__name__}: {str(e)[:160]}")
        time.sleep(3)
    log("fim da lista")


if __name__ == "__main__":
    main()
