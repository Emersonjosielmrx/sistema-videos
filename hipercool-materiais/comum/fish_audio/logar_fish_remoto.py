r"""logar_fish_remoto.py — 24/11 dona ("todos sejam workers e montadores; loga os Fish nos outros como HP Pavilion, STI
e PC2, já que eles têm as mesmas contas — é só fazer o mesmo processo do login do TikTok"; 25/11: "não faz sentido não
funcionar, você mesmo criou cada conta Fish; não é pra ter diferença entre criar e relogar").

É O MESMO login que funcionou no PC1 (login_fish.uma: fish.audio -> Cadastrar -> ícone do Google -> conta -> Continue),
trocando só ONDE o Chrome abre: em vez do Chrome do cofre do PC1, o Chrome DA CONTA na máquina (o Google já está
logado nele — netbooks_logins.json), pelo maquina_remota com proxy_fish = IP fixo do Fish da conta (rnprmtfo-N; a
máquina confere a ponte e só então abre, PROXY_OK; nunca pelo IP de casa). Logado = token (localStorage) salvo em
fish_audio\sessoes_remotas\<maquina>.json. 1 conta = 1 máquina (donos.json).
    python logar_fish_remoto.py <maquina> <email>        # ex.: sti inovaremanhwaverseesp@gmail.com
    python logar_fish_remoto.py <maquina> --lista        # contas Fish com Google logado nessa máquina
"""
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, r"D:\logins-google")
sys.path.insert(0, r"D:\postador-de-videos\bin")
DIR = AQUI / "sessoes_remotas"
DONOS = DIR / "donos.json"
LOGINS = Path(r"D:\postador-de-videos\config\netbooks_logins.json")


def log(m):
    print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)


def _ler(p, padrao):
    try:
        return json.loads(p.read_text("utf-8"))
    except (OSError, ValueError):
        return padrao


def candidatas(maquina):
    """Contas Fish (creditos.json) com o Google logado nessa máquina, que ainda não têm dono."""
    logins = _ler(LOGINS, {})
    cred = _ler(AQUI / "creditos.json", {})
    donos = _ler(DONOS, {})
    return [email for email in cred
            if (logins.get(email.split("@")[0].lower()) or {}).get(maquina, {}).get("google") and email not in donos]


def _ip_vivo(n):
    """A 1ª conexão pela ponte leva ~15 s — prazo de 90 s. IP morto = não manda a conta pra máquina."""
    import fish_audio as fa
    import urllib.request as ur
    porta = fa._subir_ponte(n)
    op = ur.build_opener(ur.ProxyHandler({"https": f"http://127.0.0.1:{porta}"}))
    for _ in range(3):
        try:
            op.open("https://fish.audio/", timeout=90).read(200)
            return True
        except Exception:  # noqa: BLE001
            time.sleep(3)
    return False


def entregar(maquina, email, n, perfil):
    """25/11: põe a conta no ~/postador-worker/fish_contas.json da máquina (é o que a fabrica_fish_linux.py serve)."""
    import maquina_remota
    rem = maquina_remota.Remoto(maquina)
    py = ("import json,pathlib,sys;p=pathlib.Path.home()/'postador-worker'/'fish_contas.json';"
          "d=json.loads(p.read_text()) if p.exists() else {};"
          f"d[{email!r}]={{'ip_n':{int(n)},'perfil':{perfil!r}}};p.write_text(json.dumps(d,indent=1));print('ENTREGUE',len(d))")
    saida = rem._txt(rem._ssh(f"python3 -c \"{py}\"", timeout=60))
    log(f"{email}: entregue à fábrica de {maquina} ({saida.strip()[-40:]})")
    return "ENTREGUE" in saida


def logar(maquina, email):
    import cofre
    import maquina_remota
    import login_fish as lf
    email = email.lower()
    donos = _ler(DONOS, {})
    if donos.get(email) and donos[email]["maquina"] != maquina:
        raise SystemExit(f"{email} já é da máquina {donos[email]['maquina']} — 1 conta = 1 máquina")
    _, e = cofre.conta(email)
    m = re.search(r"rnprmtfo-(\d+)", str(e.get("fish_proxy") or ""))
    if not m:
        raise SystemExit(f"{email}: sem fish_proxy (IP fixo do Fish) no cofre")
    n = int(m.group(1))
    if not _ip_vivo(n):
        log(f"{email}: IP Fish rnprmtfo-{n} fora (nem do PC1 responde) — pulo")
        return False
    perfil = email.split("@")[0]
    pref = f"{maquina}_{perfil}"
    rem = maquina_remota.Remoto(maquina)
    log(f"{maquina}: Chrome de {perfil} pelo IP Fish rnprmtfo-{n}")
    porta = rem.abrir(perfil, url="about:blank", proxy_fish=n)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
            ctx = b.contexts[0] if b.contexts else b.new_context()
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
            pg.set_viewport_size({"width": 1280, "height": 900})
            for _ in range(3):  # esquenta a ponte de lá (1ª conexão lenta) antes da página pesada
                try:
                    pg.goto("https://fish.audio/robots.txt", timeout=60000)
                    break
                except Exception:  # noqa: BLE001
                    time.sleep(3)
            # 25/11: "não é pra ter diferença entre criar e relogar" — a conta JÁ tem sessão no PC1 (sessoes.json:
            # token Bearer + workspace, conferida pela fábrica). Leva a MESMA sessão pro Chrome de lá (localStorage),
            # que sai pelo MESMO IP fixo da conta -> sem Google (o login por Google em máquina nova pedia confirmação
            # no celular: "Confirme que é você"). FISH_REMOTO_SO_GOOGLE=1 pula este passo.
            ses = _ler(AQUI / "sessoes.json", {}).get(email) or {}
            if ses.get("token") and not ses.get("morta") and os.environ.get("FISH_REMOTO_SO_GOOGLE") != "1":
                try:
                    if "fish.audio" not in pg.url:
                        pg.goto("https://fish.audio/robots.txt", timeout=90000)
                    pg.evaluate("""(s) => { localStorage.setItem('token', s.t);
                        if (s.w) { localStorage.setItem('active_workspace_id', s.w); } }""",
                                {"t": ses["token"], "w": ses.get("workspace")})
                    log(f"{email}: sessão do PC1 levada pro Chrome de {maquina} (sem Google)")
                except Exception as ex:  # noqa: BLE001
                    log(f"{email}: não consegui levar a sessão ({str(ex)[:100]})")
            if not lf.logado(pg):
                # === daqui pra baixo: o MESMO passo a passo do login_fish.uma (o que funcionou no PC1) ===
                pg.goto("https://fish.audio/pt/", wait_until="commit", timeout=240000)  # 25/11: conexões novas pela ponte são lentas; "commit" + espera abaixo
                try:
                    pg.wait_for_load_state("domcontentloaded", timeout=180000)
                except Exception:  # noqa: BLE001
                    pass
                time.sleep(6)
                pg.keyboard.press("Escape")
                time.sleep(1)
                try:
                    pg.get_by_role("link", name=re.compile("Cadastre-se|Inscrever|Iniciar sess", re.I)).first.click(
                        timeout=4000)
                except Exception:  # noqa: BLE001
                    pg.mouse.click(1075, 68)
                time.sleep(4)
                antes = set(ctx.pages)
                # 25/11: o Fish agora tem botão LARGO "Continuar com Google" (antes 3 ícones); clique de MOUSE no
                # centro do botão (o site ignora clique no elemento — mesma lição do login_fish)
                cx, cy = None, None
                try:
                    bt = pg.get_by_role("button", name=re.compile(r"Continu\w+ com (o )?Google|Continue with Google",
                                                                  re.I)).first
                    bx = bt.bounding_box(timeout=8000)
                    if bx:
                        cx, cy = bx["x"] + bx["width"] / 2, bx["y"] + bx["height"] / 2
                except Exception:  # noqa: BLE001
                    pass
                if cx is None:  # layout antigo: 1º dos 3 ícones sociais
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
                                gb = min((c[1] for c in linha), key=lambda b_: b_["x"])
                                cx, cy = gb["x"] + gb["width"] / 2, gb["y"] + gb["height"] / 2
                                break
                    except Exception:  # noqa: BLE001
                        pass
                pg.mouse.click(cx or 772, cy or 598)
                # o Google abre na MESMA aba ou num popup — espera um dos dois até 40 s
                g = None
                for _ in range(40):
                    novas = [x for x in ctx.pages if x not in antes]
                    g = novas[0] if novas else next((x for x in ctx.pages if "accounts.google" in x.url), None)
                    if g:
                        break
                    time.sleep(1)
                g = g or pg
                try:
                    g.wait_for_load_state("domcontentloaded", timeout=30000)
                except Exception:  # noqa: BLE001
                    pass
                time.sleep(3)
                if any(k in lf.visivel(g) for k in lf.PARAR):
                    g.screenshot(path=str(DIR / f"{pref}_PAROU.png"))
                    log(f"{email}: PAROU (captcha/confirmação) — regra: parar; ver {pref}_PAROU.png")
                    return False
                # escolher a conta: 25/11 o .click() no texto não pegava (a tela ficou no "Escolha uma conta") ->
                # clique de MOUSE no centro da linha da conta, repete enquanto o seletor seguir na tela
                for _ in range(4):
                    try:
                        if g.is_closed() or "accountchooser" not in g.url:
                            break
                        el = g.get_by_text(email, exact=False).first
                        bx = el.bounding_box(timeout=15000)
                        if bx:
                            g.mouse.click(bx["x"] + bx["width"] / 2, bx["y"] - 8)
                        else:
                            el.click(timeout=5000)
                    except Exception:  # noqa: BLE001
                        pass
                    time.sleep(6)
                try:
                    if not g.is_closed() and ("/challenge/" in g.url or any(k in lf.visivel(g) for k in lf.PARAR)):
                        g.screenshot(path=str(DIR / f"{pref}_PAROU.png"), timeout=15000)
                        log(f"{email}: Google pediu confirmação ({g.url[:60]}) — regra: parar; ver {pref}_PAROU.png")
                        return False
                except Exception:  # noqa: BLE001
                    pass
                for nome in ("Continue", "Continuar", "Allow", "Permitir"):
                    try:
                        g.get_by_role("button", name=re.compile(nome, re.I)).first.click(timeout=4000)
                        break
                    except Exception:  # noqa: BLE001
                        pass
                time.sleep(9)
            pg2 = next((x for x in ctx.pages if "fish.audio" in x.url), pg)
            try:
                pg2.wait_for_load_state("domcontentloaded", timeout=15000)
                time.sleep(4)
            except Exception:  # noqa: BLE001
                pass
            tok = ""
            for _ in range(10):
                try:
                    tok = pg2.evaluate("() => localStorage.getItem('token') || ''")
                except Exception:  # noqa: BLE001
                    tok = ""
                if tok:
                    break
                time.sleep(3)
            DIR.mkdir(exist_ok=True)
            if not tok:
                for i, x in enumerate(ctx.pages):
                    try:
                        x.screenshot(path=str(DIR / f"{pref}_fim_{i}.png"))
                        log(f"  aba {i}: {x.url[:110]}")
                    except Exception:  # noqa: BLE001
                        pass
                log(f"{email}: não logou em {maquina} — ver {pref}_fim_*.png")
                return False
            ws = None
            try:
                ws = pg2.evaluate("() => localStorage.getItem('active_workspace_id') || ''") or None
            except Exception:  # noqa: BLE001
                pass
            arq = DIR / f"{maquina}.json"
            d = _ler(arq, {})
            d[email] = {"token": tok, "workspace": ws, "fish_proxy": f"rnprmtfo-{n}",
                        "em": datetime.now().isoformat(timespec="seconds")}
            arq.write_text(json.dumps(d, ensure_ascii=False, indent=1), "utf-8")
            donos[email] = {"maquina": maquina, "em": datetime.now().isoformat(timespec="seconds")}
            DONOS.write_text(json.dumps(donos, ensure_ascii=False, indent=1), "utf-8")
            log(f"{email}: LOGADO no Fish em {maquina} (token salvo, sai pelo rnprmtfo-{n})")
            entregar(maquina, email, n, perfil)
            return True
    finally:
        rem.fechar()


if __name__ == "__main__":
    maq = sys.argv[1]
    if "--lista" in sys.argv:
        c = candidatas(maq)
        print(f"{maq}: {len(c)} contas Fish com Google logado e sem dono:")
        for x in c:
            print("  ", x)
    else:
        logar(maq, sys.argv[2])
