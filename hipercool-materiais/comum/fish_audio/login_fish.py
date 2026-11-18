"""Login inicial de UMA conta do pool no Fish Audio, pela saída fixa dela (IP rnprmtfo próprio).
fish.audio -> Cadastrar -> botão Google -> escolhe a conta na janela OAuth do Google -> Continue -> volta logado.
PARA em captcha/confirmação (conta nova com captcha = parar e avisar a dona). Print do estado em D:\tmp\fish_login.

    python login_fish.py <email_do_cofre>           # uma conta
    python login_fish.py --pool [N]                 # as próximas N contas do pool sem login (padrão: todas)
"""
import re, sys, time
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
sys.path.insert(0, r"D:\hipercool-materiais\comum\fish_audio")
import cofre  # noqa: E402
import fish_audio as fa  # noqa: E402
import pool_fish  # noqa: E402

OUT = Path(r"D:\tmp\fish_login")
OUT.mkdir(parents=True, exist_ok=True)
# só frases que aparecem NA TELA (texto visível) quando há verificação de verdade
PARAR = ("não sou um robô", "nao sou um robo", "i'm not a robot", "verify you are human", "verifique se você é humano",
         "unusual activity", "atividade incomum", "tente novamente mais tarde", "confirme que é você",
         "verify it's you", "confirme sua identidade")


def logado(pg):
    """Confiável: a página de cobrança só mostra 'My Team' + créditos restantes para quem está logado."""
    try:
        pg.goto("https://fish.audio/pt/app/billing/", wait_until="domcontentloaded", timeout=60000)
        time.sleep(8)
        t = pg.inner_text("body")
    except Exception:  # noqa: BLE001
        return False
    return "My Team" in t and "restantes" in t


def visivel(x):
    """Texto VISÍVEL da página (o código do Fish sempre carrega o script do reCAPTCHA: procurar no HTML dá falso alarme)."""
    for _ in range(10):
        try:
            x.wait_for_load_state("domcontentloaded", timeout=10000)
            return x.inner_text("body").lower()
        except Exception:  # noqa: BLE001
            time.sleep(2)
    return ""


def uma(email):
    email = email.lower()
    _, e = cofre.conta(email)
    m = re.match(r"rnprmtfo-(\d+)", str(e.get("fish_proxy") or ""))
    if not m:
        return f"{email}: SEM IP no pool"
    porta_proxy = fa._subir_ponte(int(m.group(1)))
    porta, proc = cofre.abrir(email, extra=(f"--proxy-server=127.0.0.1:{porta_proxy}",))
    pref = email.split("@")[0]
    from playwright.sync_api import sync_playwright
    try:
        with sync_playwright() as p:
            b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
            ctx = b.contexts[0]
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
            pg.set_viewport_size({"width": 1280, "height": 900})
            if logado(pg):
                return f"{email}: JÁ LOGADO"
            pg.goto("https://fish.audio/pt/", wait_until="domcontentloaded", timeout=90000)
            time.sleep(6)
            pg.keyboard.press("Escape")  # fecha popup de oferta
            time.sleep(1)
            # modal "Criar conta": link no topo direito
            try:
                pg.get_by_role("link", name=re.compile("Cadastre-se|Inscrever|Iniciar sess", re.I)).first.click(
                    timeout=4000)
            except Exception:  # noqa: BLE001
                pg.mouse.click(1075, 68)
            time.sleep(4)
            # IGUAL AO QUE FUNCIONOU NA 1ª CONTA: clique de MOUSE no CENTRO do ícone do Google (não clique no
            # elemento, que o site ignora). O Google é o 1º dos 3 ícones sociais (menor x) na linha abaixo de "ou".
            antes = set(ctx.pages)
            cx, cy = 772, 598  # fallback (posição vista nos prints)
            try:
                btns = pg.locator("button")
                trio = []
                for k in range(btns.count()):
                    bx = btns.nth(k).bounding_box()
                    if bx and 36 < bx["width"] < 70 and 36 < bx["height"] < 70:
                        trio.append((round(bx["y"]), bx))
                trio.sort(key=lambda c: c[0])
                for i in range(len(trio)):
                    linha = [c for c in trio if abs(c[0] - trio[i][0]) < 20]
                    if len(linha) >= 3:
                        g_box = min((c[1] for c in linha), key=lambda b: b["x"])  # menor x = Google
                        cx = g_box["x"] + g_box["width"] / 2
                        cy = g_box["y"] + g_box["height"] / 2
                        break
            except Exception:  # noqa: BLE001
                pass
            pg.mouse.click(cx, cy)  # clique de mouse no pixel do ícone -> vai pro Google NA MESMA ABA
            time.sleep(8)
            novas = [x for x in ctx.pages if x not in antes]
            g = novas[0] if novas else next((x for x in ctx.pages if "accounts.google" in x.url), pg)

            ler = visivel  # só texto VISÍVEL (no HTML do Fish sempre tem o script do reCAPTCHA = falso alarme)
            html = ler(g)
            if any(k in html for k in PARAR):
                g.screenshot(path=str(OUT / f"{pref}_PAROU.png"))
                return f"{email}: PAROU (captcha/confirmação) — resolver à mão: {OUT / (pref + '_PAROU.png')}"
            # escolher a conta se a janela pedir
            try:
                g.get_by_text(email, exact=False).first.click(timeout=6000)
                time.sleep(5)
            except Exception:  # noqa: BLE001
                pass
            # Continue / Permitir
            for nome in ("Continue", "Continuar", "Allow", "Permitir"):
                try:
                    g.get_by_role("button", name=re.compile(nome, re.I)).first.click(timeout=4000)
                    break
                except Exception:  # noqa: BLE001
                    pass
            time.sleep(9)
            if any(k in ler(g if not g.is_closed() else pg) for k in PARAR):
                pg.screenshot(path=str(OUT / f"{pref}_PAROU.png"))
                return f"{email}: PAROU (captcha/confirmação depois do Continue) — resolver à mão"
            pg2 = next((x for x in ctx.pages if "fish.audio" in x.url), pg)
            try:
                pg2.wait_for_load_state("domcontentloaded", timeout=15000)
                time.sleep(4)
            except Exception:  # noqa: BLE001
                pass
            try:
                pg2.bring_to_front()
            except Exception:  # noqa: BLE001
                pass
            ok = logado(pg2)
            pg2.screenshot(path=str(OUT / f"{pref}_fim.png"))
            if ok:
                cofre._marcar(email, fish_logado=time.strftime("%Y-%m-%dT%H:%M"))
            return f"{email}: {'LOGADO OK' if ok else 'CONFERIR ' + str(OUT / (pref + '_fim.png'))}"
    finally:
        try:
            cofre.fechar(proc, nome=email)
        except Exception:  # noqa: BLE001
            pass


def main():
    if sys.argv[1:2] == ["--pool"]:
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 999
        pool = pool_fish.pool_atual()
        feitas = 0
        for email in sorted(pool):
            if feitas >= n:
                break
            print(uma(email), flush=True)
            feitas += 1
            time.sleep(4)
    else:
        print(uma(sys.argv[1]))


if __name__ == "__main__":
    main()
