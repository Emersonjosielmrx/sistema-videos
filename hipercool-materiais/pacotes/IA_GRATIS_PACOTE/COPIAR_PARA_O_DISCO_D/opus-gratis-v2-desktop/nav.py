# -*- coding: utf-8 -*-
r"""nav.py — controla o Chrome da conta de teste (cofre) para conferir sites com Opus/Fable grátis.
Chrome fica aberto entre os comandos (porta do cofre); cada comando age na última aba.
  python nav.py abrir                    # abre o Chrome da conta (escondido)
  python nav.py ir <url>                 # navega, espera, imprime título + texto visível
  python nav.py texto                    # texto visível da aba
  python nav.py print <nome>             # print em D:\opus-gratis\prints\<nome>.png
  python nav.py clicar "<texto>"         # clica no 1º elemento visível com esse texto
  python nav.py css "<seletor>"          # clica pelo seletor CSS
  python nav.py escrever "<seletor>" "<texto>" [enter]
  python nav.py js "<expressão>"         # avalia JS e imprime
  python nav.py abas | aba <n>           # lista abas / passa a usar a aba n
  python nav.py fechar
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, r"D:\hipercool-materiais\comum")
try:
    import sem_janela  # noqa: F401
except ImportError:
    pass
sys.path.insert(0, r"D:\logins-google")
import cofre  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

CONTA = "sua_conta@gmail.com"
BASE = Path(r"D:\opus-gratis")
PRINTS = BASE / "prints"
ESTADO = BASE / "nav_estado.json"


def _estado():
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _texto(pg, limite=4000):
    try:
        t = pg.evaluate("() => document.body ? document.body.innerText : ''")
    except Exception:  # noqa: BLE001  (página navegando: espera e lê de novo)
        pg.wait_for_load_state("domcontentloaded")
        t = pg.evaluate("() => document.body ? document.body.innerText : ''")
    return " ".join(t.split())[:limite]


def main(a):
    cmd = a[0]
    if cmd == "abrir":
        porta, proc = cofre.abrir(CONTA)
        ESTADO.write_text(json.dumps({"porta": porta, "aba": -1, "pid": proc.pid if proc else None}), encoding="utf-8")
        print("PRONTO porta", porta)
        return
    st = _estado()
    porta = st["porta"]
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        ctx = br.contexts[0]
        if cmd == "fechar":
            try:
                br.new_browser_cdp_session().send("Browser.close")
            except Exception:  # noqa: BLE001
                pass
            print("fechado")
            return
        pags = ctx.pages or [ctx.new_page()]
        if cmd == "abas":
            for i, pg in enumerate(pags):
                print(i, pg.url[:120], "|", pg.title()[:60])
            return
        if cmd == "aba":
            st["aba"] = int(a[1])
            ESTADO.write_text(json.dumps(st), encoding="utf-8")
            print("usando aba", a[1], pags[int(a[1])].url[:120])
            return
        pg = pags[st.get("aba", -1)] if -len(pags) <= st.get("aba", -1) < len(pags) else pags[-1]
        pg.bring_to_front()  # aba de fundo não desenha: print e clique travam
        if cmd == "ir":
            pg.goto(a[1], wait_until="domcontentloaded", timeout=60000)
            time.sleep(float(a[2]) if len(a) > 2 else 6)
            print("URL:", pg.url, "| TÍTULO:", pg.title())
            print(_texto(pg))
        elif cmd == "texto":
            print("URL:", pg.url)
            print(_texto(pg, int(a[1]) if len(a) > 1 else 6000))
        elif cmd == "print":
            PRINTS.mkdir(parents=True, exist_ok=True)
            f = PRINTS / f"{a[1]}.png"
            pg.screenshot(path=str(f))
            print(f)
        elif cmd == "clicar":
            pg.get_by_text(a[1], exact=False).locator("visible=true").first.click(timeout=15000)
            time.sleep(float(a[2]) if len(a) > 2 else 4)
            print("URL:", pg.url)
            print(_texto(pg, 1500))
        elif cmd == "css":
            pg.locator(a[1]).locator("visible=true").first.click(timeout=15000)
            time.sleep(float(a[2]) if len(a) > 2 else 4)
            print("URL:", pg.url)
            print(_texto(pg, 1500))
        elif cmd == "escrever":
            el = pg.locator(a[1]).locator("visible=true").first
            el.click(timeout=15000)
            el.fill(a[2]) if el.evaluate("e => e.tagName") in ("INPUT", "TEXTAREA") else pg.keyboard.type(a[2])
            if len(a) > 3 and a[3] == "enter":
                pg.keyboard.press("Enter")
            print("escrito")
        elif cmd == "js":
            print(json.dumps(pg.evaluate(a[1]), ensure_ascii=False)[:6000])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main(sys.argv[1:])
