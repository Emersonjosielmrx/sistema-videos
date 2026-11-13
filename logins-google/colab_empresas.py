"""Entra na Colab com a conta Google de cada empresa (Chrome do cofre) e tira print. Uma Colab por empresa.

  python colab_empresas.py            # todas
  python colab_empresas.py msenergypara
Prints em D:\\logins-google\\colab_prints\\
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
import cofre
from playwright.sync_api import sync_playwright

EMPRESAS = {
    "inovaremultiatendimento": "Inovare",
    "msenergypara": "MS Energy",
    "fabricadeautomacoesia": "Fábrica de Automações",
    "seebotsia": "SeeBots IA",
    "mentoriaiapro": "Mentoria IA Pro",
    "mundosolar1995": "Mundo Solar",
}
PRINTS = Path(__file__).resolve().parent / "colab_prints"
ESTADO = Path(r"D:\video-fila\estado\colab_contas.json")  # lido pelo maquinas.py -> card COLAB do painel :8790
ACEITAR = ("Aceitar", "Accept", "Concordo", "I agree", "Continuar", "Continue")


def entrar(conta):
    porta, proc = cofre.abrir(conta)
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        pg = br.contexts[0].new_page()
        pg.goto("https://colab.research.google.com/", wait_until="domcontentloaded", timeout=90000)
        time.sleep(10)
        for txt in ACEITAR:  # termos da primeira vez, se aparecer
            b = pg.get_by_role("button", name=txt, exact=True)
            if b.count() and b.first.is_visible():
                b.first.click()
                time.sleep(3)
        PRINTS.mkdir(exist_ok=True)
        pg.screenshot(path=str(PRINTS / f"{conta}.png"))
        logado = pg.locator('a[href*="SignOutOptions"], a[aria-label*="Conta do Google"], '
                            'a[aria-label*="Google Account"]').count() > 0
        entrar_btn = pg.get_by_text("Fazer login", exact=True).count() + pg.get_by_text("Sign in", exact=True).count()
        pg.close()
        cofre.fechar(proc, br, conta)
    return logado and not entrar_btn


if __name__ == "__main__":
    if sys.argv[1:] == ["--resto"]:  # todas as contas vivas do cofre que ainda não estão acima (nem a 649)
        reg = cofre._ler()["contas"]
        contas = [e.split("@")[0] for e, d in reg.items() if d.get("google") == "vivo"
                  and e.split("@")[0] not in EMPRESAS and e.split("@")[0] != "emersonjosiel649"]
    else:
        contas = sys.argv[1:] or list(EMPRESAS)
    try:
        est = json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        est = {"contas": []}
    por = {c["conta"]: c for c in est["contas"]}
    for conta in contas:
        try:
            ok, erro = entrar(conta), ""
            print(f"{EMPRESAS.get(conta, conta):24} {conta:26} {'LOGADA' if ok else 'conferir print'}", flush=True)
        except Exception as e:
            ok, erro = False, str(e)[:120]
            print(f"{EMPRESAS.get(conta, conta):24} {conta:26} ERRO {erro}", flush=True)
        por[conta] = {**por.get(conta, {}), "conta": conta, "empresa": EMPRESAS.get(conta, ""), "logada": ok,
                      "erro": erro, "visto": datetime.now().strftime("%d/%m %H:%M")}
        est = {"em": datetime.now().isoformat(timespec="seconds"), "contas": sorted(por.values(), key=lambda c: c["conta"])}
        ESTADO.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")
