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
import json, re, socket, subprocess, sys, time
from pathlib import Path

BIN = Path(__file__).resolve().parent
CFG = BIN.parent / "config" / "facebook_paginas.json"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def cfg():
    return json.loads(CFG.read_text(encoding="utf-8"))


def _porta_aberta(porta):
    s = socket.socket(); r = s.connect_ex(("127.0.0.1", porta)) == 0; s.close(); return r


def abrir(conta):
    """Garante o Chrome da conta aberto pela saída fixa. Devolve (porta_cdp, proc_ou_None_se_ja_estava)."""
    c = cfg()["contas"][conta]
    porta = c["porta"]
    if _porta_aberta(porta):
        _conferir_saida(conta)
        return porta, None
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
        _, proc = cofre.abrir(c["email"], extra=(f"--proxy-server=127.0.0.1:{px}",))
    for _ in range(40):
        if _porta_aberta(porta):
            break
        time.sleep(0.5)
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


def listar_paginas(ctx):
    """Páginas do perfil logado (atalhos + /pages). Devolve [(nome, url)]."""
    pg = ctx.new_page()
    achou = {}
    try:
        for url in ("https://www.facebook.com/pages/?category=your_pages", "https://www.facebook.com/bookmarks/pages"):
            pg.goto(url, wait_until="domcontentloaded", timeout=45000)
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
