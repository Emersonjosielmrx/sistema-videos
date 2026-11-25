"""Contas do Facebook usadas nas Páginas (dona 19-20/11/2026): abre o Chrome certo de cada conta, SEMPRE pela saída
fixa dela, e lista as páginas.

Contas (config/facebook_paginas.json):
  msenergypara   = perfil antigo (FB 100034440531020), Chrome D:\\logins-google\\chrome-profiles\\msenergypara, porta 9401,
                   saída = casa (é a saída de sempre dele: o postar_ms_energy já posta por aqui desde 08/2026).
  emersonjosiel02 = perfil novo (FB 61596623373095), Chrome do cofre emersonjosiel02@gmail.com, porta 9798,
                   saída = Webshare rnprmtfo-58 (fish_proxy no cofre). NUNCA por casa.
Nunca abrir as duas pela mesma saída (regra NUNCA 2 contas no mesmo IP).

    python fb_contas.py paginas <conta>      # lista as páginas da conta (abre e fecha o Chrome se não estava aberto)
"""
import json, os, re, socket, subprocess, sys, time
from pathlib import Path

BIN = Path(__file__).resolve().parent
CFG = BIN.parent / "config" / "facebook_paginas.json"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def cfg():
    return json.loads(CFG.read_text(encoding="utf-8"))


def _porta_aberta(porta):
    s = socket.socket(); r = s.connect_ex(("127.0.0.1", porta)) == 0; s.close(); return r


def _pids_do_perfil(conta):
    """PIDs dos Chrome (processo principal) desta conta: pela porta CDP ou pela pasta do perfil."""
    c = cfg()["contas"][conta]
    chave = c.get("perfil") or f"remote-debugging-port={c['porta']}"
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "Get-CimInstance Win32_Process -Filter \"name='chrome.exe'\" | ? { $_.CommandLine -notmatch '--type=' "
                          f"-and ($_.CommandLine -match 'remote-debugging-port={c['porta']}' -or $_.CommandLine -like '*{chave}*') }}"
                          " | % { $_.ProcessId }"], capture_output=True, text=True).stdout
    return [int(x) for x in out.split() if x.isdigit()]


def _chrome_alheio(c):
    """'porta N' se há um Chrome principal no MESMO perfil (pasta real, seguindo junction) numa porta que não é a nossa."""
    if not c.get("perfil"):
        return None
    real = os.path.realpath(c["perfil"]).casefold()
    alias = {real, c["perfil"].casefold()}
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "Get-CimInstance Win32_Process -Filter \"name='chrome.exe'\" | ? { $_.CommandLine -notmatch '--type=' } "
                          "| % { $_.CommandLine }"], capture_output=True, text=True).stdout
    for linha in out.splitlines():
        m = re.search(r'--user-data-dir="?([^"]+?)"?(?:\s--|$)', linha)
        if m and (m.group(1).casefold() in alias or os.path.realpath(m.group(1)).casefold() == real) \
                and f"remote-debugging-port={c['porta']}" not in linha:
            p = re.search(r"remote-debugging-port=(\d+)", linha)
            return f"porta {p.group(1) if p else '?'}"
    return None


def abrir(conta, _tentativa=0):
    """Garante o Chrome da conta aberto pela saída fixa. Devolve (porta_cdp, proc_ou_None_se_ja_estava)."""
    c = cfg()["contas"][conta]
    porta = c["porta"]
    if _porta_aberta(porta):
        _conferir_saida(conta)
        return porta, None
    # 20/11 13h: chrome-profiles\msenergypara é JUNCTION para cofre\perfis\msenergypara — a fábrica do Fish
    # (fabrica_fish.py) abre o MESMO perfil por outra porta (97xx, proxy rnprmtfo-37). Chrome dela aberto = perfil em
    # uso (código 21): NÃO mata (é de outro projeto e por outra saída); a vez do Facebook fica pra próxima.
    alheio = _chrome_alheio(c)
    if alheio:
        raise RuntimeError(f"{conta}: o perfil está aberto por outro programa ({alheio}) — Facebook espera a próxima")
    # 20/11 12h: Chrome do perfil ainda morrendo (sem porta) fazia o novo entregar pra ele e sair -> porta nunca abria
    # (ECONNREFUSED na MS Energy 11:05 e no criar_fila). Sem porta = nenhum Chrome deste perfil pode estar vivo.
    for pid in _pids_do_perfil(conta):
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
        time.sleep(3)
    if c["saida"] == "casa":
        proc = subprocess.Popen([CHROME, f"--remote-debugging-port={porta}", f"--user-data-dir={c['perfil']}",
                                 "--no-first-run", "--no-default-browser-check", "--remote-allow-origins=*",
                                 "--window-position=-2000,0", "--window-size=1280,900", "about:blank"])
    else:  # webshare rnprmtfo-N via cofre (mesma ponte do Fish)
        sys.path.insert(0, r"D:\logins-google"); sys.path.insert(0, r"D:\hipercool-materiais\comum\fish_audio")
        import fish_audio
        cofre, n = fish_audio.checar_conta(c["email"])
        if f"rnprmtfo-{n}" != c["saida"]:
            raise SystemExit(f"{conta}: saída do cofre rnprmtfo-{n} != configurada {c['saida']}")
        px = fish_audio._subir_ponte(n)
        # 24/11 (noite, pc1.1): Chrome do FB mais leve no PC1 (100% de CPU com render): limita processos de página e
        # desliga recursos inúteis (iguais ao netbooks/chrome_conta.LEVE). FB_CHROME_PESADO=1 volta ao antigo.
        leve = () if os.environ.get("FB_CHROME_PESADO") == "1" else (
            "--renderer-process-limit=3", "--disable-features=Translate,MediaRouter,OptimizationHints",
            "--disable-component-update", "--mute-audio")
        _, proc = cofre.abrir(c["email"], extra=(f"--proxy-server=127.0.0.1:{px}",) + leve)
    # 20/11: o Chrome do perfil antigo às vezes leva >20 s pra responder o CDP (ECONNRESET no connect_over_cdp)
    import urllib.request
    for _ in range(120):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{porta}/json/version", timeout=3).read()
            break
        except Exception:
            time.sleep(0.5)
    else:
        fechar(proc)
        if _tentativa == 0:
            return abrir(conta, 1)
        raise RuntimeError(f"{conta}: o Chrome não abriu a porta {porta} (2 tentativas)")
    time.sleep(3)
    _conferir_saida(conta)
    return porta, proc


def _conferir_saida(conta):
    """Recusa se o Chrome aberto na porta não está com a saída certa (proxy da conta ou casa sem proxy)."""
    c = cfg()["contas"][conta]
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          f"(Get-CimInstance Win32_Process -Filter \"name='chrome.exe'\" | ? {{ $_.CommandLine -match "
                          f"'remote-debugging-port={c['porta']}' -and $_.CommandLine -notmatch '--type=' }}).CommandLine"],
                         capture_output=True, text=True).stdout
    tem_proxy = "--proxy-server=127.0.0.1:" in out
    if c["saida"] == "casa" and tem_proxy:
        raise SystemExit(f"{conta}: Chrome aberto com proxy, esperado casa")
    if c["saida"] != "casa":
        n = int(c["saida"].split("-")[1])
        if f"--proxy-server=127.0.0.1:{18500 + n}" not in out:
            raise SystemExit(f"{conta}: Chrome da porta {c['porta']} NÃO está na saída {c['saida']} — recuso")


def fechar(proc):
    if proc:
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
        # 20/11 11:05 (MS Energy): reabrir o mesmo perfil logo depois dava ECONNREFUSED — espera o Chrome sair de verdade
        for _ in range(30):
            out = subprocess.run(["tasklist", "/FI", f"PID eq {proc.pid}", "/NH", "/FO", "CSV"], capture_output=True).stdout
            if str(proc.pid).encode() not in (out or b""):
                break
            time.sleep(0.5)
        time.sleep(4)


def listar_paginas(ctx):
    """Páginas do perfil logado (atalhos + /pages). Devolve [(nome, url)]."""
    pg = ctx.new_page()
    achou = {}
    try:
        for url in ("https://www.facebook.com/pages/?category=your_pages", "https://www.facebook.com/bookmarks/pages"):
            pg.goto(url, wait_until="domcontentloaded", timeout=120000)  # 23/11: 45 s estourava (proxy + PC1 cheio)
            time.sleep(6)
            for t, h in pg.eval_on_selector_all("a[href]", "els => els.map(e => [e.innerText.trim().split('\\n')[0].slice(0,60), e.href])"):
                h = h.split("&")[0].split("?__")[0]
                if t and ("profile.php?id=" in h or re.match(r"https://www\.facebook\.com/[A-Za-z0-9.\-]+/?$", h)) and not any(
                        x in h for x in ("/friends", "/notifications", "/watch", "/marketplace", "/groups", "/gaming", "/pages",
                                         "/bookmarks", "/events", "/memories", "/saved", "/reel", "/ads", "/business",
                                         "/fundraisers", "/messages", "/settings", "/help", "/policies", "/privacy")):
                    achou.setdefault(h, t)
    finally:
        pg.close()
    return [(t, h) for h, t in achou.items()]


if __name__ == "__main__":
    if sys.argv[1:2] == ["paginas"]:
        from playwright.sync_api import sync_playwright
        porta, proc = abrir(sys.argv[2])
        try:
            with sync_playwright() as p:
                b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
                ctx = b.contexts[0]
                ck = {x["name"]: x["value"] for x in ctx.cookies("https://www.facebook.com")}
                print("logado:", "c_user" in ck, ck.get("c_user"))
                for t, h in listar_paginas(ctx):
                    print(repr(t), h)
        finally:
            fechar(proc)
