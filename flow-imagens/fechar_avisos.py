# Dona 06/11: "chegou aviso em todos os veo3, o aviso tem que ser fechado senão ele não faz; tem que ter vigilância via
# print pra serem resolvidos sempre que aparecerem". Ex.: modal "Introducing Omni 1.2!" travava os Chrome do Flow do PC2.
# Para cada máquina/porta CDP: abre túnel ssh, olha cada aba do Flow/labs.google, tira print, fecha diálogo/modal
# (botão de fechar/ok/entendi ou Esc), tira print depois. NUNCA mexe em verificação de idade (só registra).
#   python fechar_avisos.py            -> todas as máquinas
#   python fechar_avisos.py pc2        -> uma
# Esta é a 3ª camada. As 1ªs fecham na hora: fabrica_tokens._fechar_novidades (Chrome quente do PC2/desktop) e
# gera_auto._fechar_modal_novidades (Chrome por imagem). Aviso novo de outro tipo: pôr a palavra nas 3.
# Só interage com a página local de cada Chrome (cada Chrome já sai pela saída dele); não abre conta nem navega.
import json
import socket
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).parent
PRINTS = AQUI / "prints_avisos"
LOG = AQUI / "fechar_avisos.log"
SSH_PC2 = ["-i", r"C:\Users\Haylla\.ssh\id_rsa_pc2", "-o", "IdentitiesOnly=yes", "Emerson-IA@192.168.18.7"]
MAQ = {
    "pc2": (SSH_PC2, list(range(9470, 9477)) + list(range(9480, 9490)) + [9460]),
    "desktop": (["desktop"], list(range(9470, 9477)) + list(range(9480, 9490)) + [9460]),
    # mesma conexão de maquina_remota.MAQUINAS (postador-de-videos\bin)
    "x200ma": (["-p", "2222", "emerson@100.87.195.108"], [9460, 9470, 9471, 9472]),
    "acer": (["emerson-ia@100.98.55.125"], [9460, 9470, 9471, 9472]),
}
# 06/11: janela de cadastro do Flow ("Experience and shape AI tools", Sign out / Next) — Esc não fecha; avança com
# Next/Avançar sem marcar e-mail de marketing. NUNCA "Sign out"/"Sair" (não está na lista de propósito).
BOTOES = ["Next", "Avançar", "Close", "Got it", "Dismiss", "OK", "Okay", "Done", "Not now", "No thanks", "Skip", "Maybe later",
          "Continue", "Fechar", "Entendi", "Ok", "Agora não", "Não, obrigado", "Pular", "Continuar", "Concluído"]
IDADE = ("verify your age", "verifique sua idade", "age verification", "confirm your age", "idade")

JS_DIALOGOS = r"""() => {
  const vis = e => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
    return r.width > 50 && r.height > 50 && s.visibility !== 'hidden' && s.display !== 'none' && s.opacity !== '0'; };
  const ds = [...document.querySelectorAll('[role=dialog],[role=alertdialog],dialog[open],[aria-modal=true]')].filter(vis);
  return ds.map(d => ({texto: (d.innerText || '').slice(0, 300),
    botoes: [...d.querySelectorAll('button,[role=button],a')].filter(vis2 => true)
      .map(b => (b.getAttribute('aria-label') || b.innerText || '').trim().slice(0, 40)).filter(Boolean).slice(0, 15)}));
}"""


def flow(url):
    # 06/11: o Flow mudou para flow.google.com (antes labs.google/fx)
    return any(d in (url or "") for d in ("flow.google", "labs.google"))


def log(m):
    linha = f"{datetime.now():%Y-%m-%d %H:%M:%S} {m}"
    print(linha, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def livre():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def portas_abertas(ssh, portas):
    """Uma conexão só pergunta quais portas CDP estão escutando (rajada de ssh trava o desktop)."""
    import re
    try:
        r = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10"] + ssh + ["netstat -an"],
                           capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL,
                           creationflags=0x08000000)
        abertas = {int(x) for x in re.findall(r"127\.0\.0\.1:(\d+)\s+\S+\s+(?:LISTENING|OUÇANDO|ESCUTANDO)",
                                              r.stdout or "")}
        if not abertas:  # linux (s20 etc.) / outra língua
            abertas = {int(x) for x in re.findall(r"127\.0\.0\.1:(\d+)", r.stdout or "")}
    except Exception:  # noqa: BLE001
        return []
    return [p for p in portas if p in abertas]


def print_cdp(pg, nome):
    """Print pelo CDP direto (pg.screenshot travava em 'waiting for fonts' na 9484)."""
    import base64
    try:
        s = pg.context.new_cdp_session(pg)
        d = s.send("Page.captureScreenshot", {"format": "jpeg", "quality": 60})
        (PRINTS / nome).write_bytes(base64.b64decode(d["data"]))
        s.detach()
    except Exception:  # noqa: BLE001
        pass


def fechar_na_pagina(pg, rotulo):
    ds = pg.evaluate(JS_DIALOGOS)
    if not ds:
        return "limpa"
    tudo = " ".join(d["texto"] for d in ds).lower()
    if any(k in tudo for k in IDADE):
        return "IDADE (não mexo): " + tudo[:80].replace("\n", " ")
    hora = f"{datetime.now():%d%m_%H%M%S}"
    print_cdp(pg, f"{rotulo}_{hora}_antes.jpg")
    feito = ""
    for _ in range(4):
        ok = False
        # 06/11: "Review our privacy policy" deixa o Continue desabilitado até rolar o texto até o fim
        try:
            pg.evaluate("""() => document.querySelectorAll('[role=dialog] *, [aria-modal=true] *').forEach(e => {
                if (e.scrollHeight > e.clientHeight + 5) e.scrollTop = e.scrollHeight; })""")
            time.sleep(1)
        except Exception:  # noqa: BLE001
            pass
        for nome in BOTOES:
            for loc in (pg.locator(f"[role=dialog] button[aria-label='{nome}'], [aria-modal=true] button[aria-label='{nome}']"),
                        pg.locator("[role=dialog], [aria-modal=true], dialog[open]").get_by_role(
                            "button", name=nome, exact=True)):
                try:
                    if loc.count() and loc.first.is_visible():
                        loc.first.click(timeout=4000)
                        feito += f"[{nome}]"
                        ok = True
                        break
                except Exception:  # noqa: BLE001
                    pass
            if ok:
                break
        if not ok:
            pg.keyboard.press("Escape")
            feito += "[Esc]"
        time.sleep(1.5)
        if not pg.evaluate(JS_DIALOGOS):
            break
    resto = pg.evaluate(JS_DIALOGOS)
    print_cdp(pg, f"{rotulo}_{hora}_depois.jpg")
    titulo = ds[0]["texto"][:60].replace("\n", " ")
    return f"aviso '{titulo}' {feito} -> {'FECHADO' if not resto else 'CONTINUA: ' + str(resto[0]['botoes'])}"


def passada(maq):
    from playwright.sync_api import sync_playwright
    ssh, portas = MAQ[maq]
    # 06/11: no PC2 o ssh com comando não encerra (fica pendurado) -> sem consulta; túnel com todas as candidatas,
    # porta fechada só falha rápido no urlopen
    abertas = portas
    # um túnel só com todas as portas (1 conexão por máquina)
    mapa = {p: livre() for p in abertas}
    fw = sum((["-L", f"{l}:127.0.0.1:{p}"] for p, l in mapa.items()), [])
    t = subprocess.Popen(["ssh", "-N", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15"] + fw + ssh,
                         stdin=subprocess.DEVNULL, creationflags=0x08000000)
    time.sleep(4)
    res = {}
    try:
        with sync_playwright() as pw:
            for porta, loc in mapa.items():
                try:
                    try:
                        abas = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{loc}/json", timeout=8).read())
                    except OSError:
                        continue  # porta sem Chrome
                    res[str(porta)] = "vista"
                    if not any(flow(a.get("url")) for a in abas if a.get("type") == "page"):
                        continue
                    b = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{loc}", timeout=20000)
                    for ctx in b.contexts:
                        for i, pg in enumerate(ctx.pages):
                            if not flow(pg.url):
                                continue
                            r = fechar_na_pagina(pg, f"{maq}_{porta}_{i}")
                            res[f"{porta}/{i}"] = r
                            if r != "limpa":
                                log(f"{maq} {porta} aba{i}: {r}")
                except Exception as e:  # noqa: BLE001
                    res[str(porta)] = f"erro {type(e).__name__}: {str(e)[:80]}"
                    log(f"{maq} {porta}: erro {type(e).__name__}: {str(e)[:120]}")
    finally:
        t.terminate()
    log(f"{maq}: {sum(1 for k in res if '/' not in k)} Chrome vistos, {sum(1 for v in res.values() if 'FECHADO' in v)} avisos fechados, "
        f"{sum(1 for v in res.values() if 'CONTINUA' in v)} continuam")
    return res


if __name__ == "__main__":
    PRINTS.mkdir(exist_ok=True)
    for m in (sys.argv[1:] or list(MAQ)):
        try:
            passada(m)
        except Exception as e:  # noqa: BLE001
            log(f"{m}: erro geral {type(e).__name__}: {e}")
