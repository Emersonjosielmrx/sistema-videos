r"""
Fila de login no Google para a dona: abre uma conta por vez no Chrome do cofre, digita o e-mail e clica Avancar;
a pessoa digita a senha (e a verificacao). Quando o login entra, marca google=vivo no cofre, fecha e abre a proxima.

  python logar_fila.py kiro            # contas da kiro_contas_unica.json que nao estao vivas no cofre
  python logar_fila.py a@gmail.com b@gmail.com
Espera ate 15 min por conta; se passar, pula para a proxima (fica para depois).
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cofre

DIR = Path(__file__).resolve().parent
ESPERA_MAX = 15 * 60


def _pendentes_kiro():
    kiro = json.loads((DIR / "kiro_contas_unica.json").read_text(encoding="utf-8"))["contas"]
    reg = cofre._ler()["contas"]
    return [e for e in kiro if "@" in e and reg.get(e, {}).get("google") != "vivo"
            and not kiro[e].get("bloqueada_novo_login")]


def _bloqueadas():
    kiro = json.loads((DIR / "kiro_contas_unica.json").read_text(encoding="utf-8"))["contas"]
    return {e for e, v in kiro.items() if v.get("bloqueada_novo_login")}


def _logado(ctx, page):
    url = page.url
    if "accounts.google.com" in url and any(t in url for t in ("signin", "challenge", "ServiceLogin", "speedbump")):
        return False
    return any(c["name"] == "SID" and c["domain"].endswith("google.com") for c in ctx.cookies())


def logar_um(email):
    from playwright.sync_api import sync_playwright
    try:
        cofre.conta(email)
    except KeyError:
        cofre.registrar(email)
    porta, proc = cofre.abrir(email, "https://accounts.google.com/signin", visivel=True)
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        ctx = br.contexts[0]
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        time.sleep(4)
        if _logado(ctx, page):
            print("  ja estava logada", flush=True)
        else:
            try:
                campo = page.locator('input[name="identifier"], input[type="email"]').first
                campo.wait_for(state="visible", timeout=20000)
                campo.fill(email)
                page.locator("#identifierNext button, #identifierNext").first.click(timeout=10000)
                print("  e-mail digitado -> digite a SENHA na janela do Chrome", flush=True)
            except Exception:
                print("  nao achei o campo de e-mail; faca o login na janela", flush=True)
        inicio = time.time()
        ok = False
        while time.time() - inicio < ESPERA_MAX:
            try:
                if _logado(ctx, page):
                    ok = True
                    break
            except Exception:
                pass
            time.sleep(3)
        agora = datetime.now().isoformat(timespec="minutes")
        if ok:
            cofre._marcar(email, google="vivo", checado=agora)
            time.sleep(3)
        cofre.fechar(proc, br, nome=email)
        return ok


def main(args):
    lista = _pendentes_kiro() if args[:1] == ["kiro"] else args
    proibidas = [e for e in lista if e.lower() in _bloqueadas()]
    if proibidas:
        print(f"PULANDO {len(proibidas)} conta(s) bloqueada(s) para login novo (so usar onde ja estao logadas): "
              f"{', '.join(proibidas)}", flush=True)
        lista = [e for e in lista if e not in proibidas]
    print(f"{len(lista)} conta(s) para logar", flush=True)
    feitas, puladas = [], []
    for i, email in enumerate(lista, 1):
        print(f"\n[{i}/{len(lista)}] {email}", flush=True)
        try:
            (feitas if logar_um(email) else puladas).append(email)
        except Exception as e:
            print(f"  erro: {str(e)[:150]}", flush=True)
            puladas.append(email)
        print(f"  -> {'LOGADA' if email in feitas else 'PULADA (ficou para depois)'}", flush=True)
    print(f"\nFim: {len(feitas)} logadas, {len(puladas)} para depois: {', '.join(puladas)}", flush=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
    else:
        main(sys.argv[1:])
