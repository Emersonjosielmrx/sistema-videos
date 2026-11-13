#!/usr/bin/env python3
"""kiro_creditos.py — confere, conta por conta do cofre, se ela já usa o Kiro e quantos créditos tem (dona 23/10/2026:
"basta entrar em todas e conferir os créditos; crie um script pra isso, já que podemos precisar outras vezes").

Para cada conta com Google vivo no cofre (D:\\logins-google\\cofre\\contas.json):
  app.kiro.dev -> recusa os cookies opcionais ("Decline") -> "Google" -> escolhe a conta já logada no perfil.
  - O Google volta direto pro Kiro: a conta JÁ usa o Kiro -> lê os créditos na página da conta e sai (Sign out).
  - O Google pede "Fazer login no serviço kiro... / Continuar": é a 1ª vez dessa conta no Kiro (ou o acesso foi
    removido). Clicar em Continuar CRIARIA uma conta nova: o script clica em CANCELAR e anota "sem_kiro".
  - Cadastro/termos/onboarding do Kiro depois do login: não aceita nada, anota "pediu_cadastro" e sai.
Contas que aparecem no seletor do Google do perfil e NÃO estão no cofre: só são listadas (nunca entra nelas).
Senha nunca. Resultado: kiro_creditos.json (última leitura por conta) e KIRO_CREDITOS.md (tabela pra ler).

    python kiro_creditos.py                 # todas as contas com Google vivo
    python kiro_creditos.py conta1 conta2   # só essas (e-mail ou apelido)
    python kiro_creditos.py --relatorio     # só refaz a tabela com a última leitura
    python kiro_creditos.py --abrir conta1 conta2   # conta sem Kiro: janela NA TELA na permissão do Google (a dona
                                                    # clica em Continuar; o script nunca aceita)
    python kiro_creditos.py --fila [feitas...]      # abre 5 por vez as que precisam da dona; fechou uma, abre a próxima
"""
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import cofre  # noqa: E402

SAIDA = BASE / "kiro_creditos.json"
RELATORIO = BASE / "KIRO_CREDITOS.md"
PRINTS = BASE / "kiro_prints"
KIRO = "https://app.kiro.dev/"


def _ler():
    try:
        return json.loads(SAIDA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _gravar(d):
    tmp = SAIDA.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(SAIDA)


def _texto(pg):
    try:
        return " | ".join(x.strip() for x in pg.inner_text("body", timeout=10000).split("\n") if x.strip())
    except Exception:  # noqa: BLE001
        return ""


def _creditos(txt):
    """Da página Settings > Account & plan (conferida 23/10, aulacomia): "Estimated Usage | resets on 10/31 | Kiro Free |
    Total credits used this month: 0 | Credits | 0 used / 50 covered in plan"."""
    out = {}
    m = re.search(r"([\d.,]+)\s*used\s*/\s*([\d.,]+)\s*covered", txt, re.I)
    if m:
        out["usados"], out["limite"] = m.group(1), m.group(2)
        try:
            out["restantes"] = str(round(float(m.group(2).replace(",", "")) - float(m.group(1).replace(",", "")), 1))
        except ValueError:
            pass
    m = re.search(r"Total credits used this month:\s*([\d.,]+)", txt, re.I)
    if m:
        out["usados_mes"] = m.group(1)
    m = re.search(r"Estimated Usage\s*\|?\s*(?:\|\s*)*resets on\s*([\d/]+)\s*\|\s*(Kiro [A-Za-z+ ]+?)\s*\|", txt, re.I)
    if m:
        out["renova"], out["plano"] = m.group(1), m.group(2).strip()
    else:
        m = re.search(r"resets on\s*([\d/]+)", txt, re.I)
        if m:
            out["renova"] = m.group(1)
    return out


def _recusar_cookies(pg):
    try:
        pg.get_by_role("button", name="Decline").click(timeout=5000)
        pg.wait_for_timeout(1500)
    except Exception:  # noqa: BLE001
        pass


RAM_MIN_GB = 3.0  # deixa janela aberta só enquanto sobrar isso de RAM livre (o PC1 renderiza)


def _ram_livre_gb():
    try:
        import ctypes

        class M(ctypes.Structure):
            _fields_ = [("l", ctypes.c_ulong), ("c", ctypes.c_ulong), ("t", ctypes.c_ulonglong),
                        ("a", ctypes.c_ulonglong), ("x", ctypes.c_ulonglong * 5)]
        m = M()
        m.l = ctypes.sizeof(M)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        return m.a / 1e9
    except Exception:  # noqa: BLE001
        return 99.0


def _na_tela(br, pg):
    try:
        s = br.contexts[0].new_cdp_session(pg)
        jan = s.send("Browser.getWindowForTarget")["windowId"]
        s.send("Browser.setWindowBounds", {"windowId": jan, "bounds": {"windowState": "normal"}})
        s.send("Browser.setWindowBounds", {"windowId": jan, "bounds": {"left": 60, "top": 40, "width": 1280, "height": 900}})
        pg.bring_to_front()
    except Exception:  # noqa: BLE001
        pass


def conferir(email, p, deixar=False):
    """deixar=True (dona 23/10: "deixa aberto as que tiverem crédito e as que precisam cadastrar"): conta com crédito
    fica com a janela NA TELA na página do plano; conta sem Kiro fica NA TELA parada no "Continuar" do Google (quem
    clica é a dona). As outras fecham."""
    porta, proc = cofre.abrir(email)
    br = None
    res = {"em": datetime.now().isoformat(timespec="minutes")}
    manter = False
    try:
        br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        pg = br.contexts[0].new_page()
        pg.set_viewport_size({"width": 1280, "height": 900})
        pg.goto(KIRO, wait_until="domcontentloaded", timeout=90000)
        pg.wait_for_timeout(6000)
        if "signin" in pg.url:
            try:
                pg.get_by_role("button", name="Decline").click(timeout=5000)
            except Exception:  # noqa: BLE001
                pass
            pg.get_by_text("Google", exact=True).first.click()
            pg.wait_for_timeout(8000)
            if "accountchooser" in pg.url:
                outras = [x for x in pg.locator("[data-identifier]").evaluate_all(
                    "els => els.map(e => e.getAttribute('data-identifier'))") if x and x.lower() != email]
                if outras:
                    res["outras_contas_no_perfil"] = outras
                alvo = pg.locator(f'[data-identifier="{email}"]').first
                if not alvo.count():
                    res["situacao"] = "conta_fora_do_seletor"
                    return res
                alvo.click()
            fim = time.time() + 45
            while time.time() < fim and ("accounts.google.com" in pg.url or "amazoncognito" in pg.url):
                txt = _texto(pg)
                # 1ª vez desta conta no Kiro: "Continuar" criaria a conta — cancela e anota
                # pt e en (23/10: e4487017 tem o Google em inglês — "Google will allow ... to access")
                if re.search(r"vai permitir que .{0,80}amazoncognito|will allow .{0,80}amazoncognito|wants to access|"
                             r"Fazer login no servi|Sign in to kiro", txt, re.I) \
                        and pg.get_by_role("button", name=re.compile(r"^(Continuar|Continue)$")).count():
                    res["situacao"] = "sem_kiro"
                    if deixar:  # fica na tela, no "Continuar", pra dona decidir
                        manter = res["janela_aberta"] = True
                        _na_tela(br, pg)
                        return res
                    try:
                        pg.get_by_role("button", name=re.compile(r"^(Cancelar|Cancel)$")).first.click(timeout=5000)
                    except Exception:  # noqa: BLE001
                        pass
                    return res
                if re.search(r"Digite sua senha|Enter your password|Verifique se é você|Verify it", txt, re.I):
                    res["situacao"] = "google_pediu_login"
                    return res
                pg.wait_for_timeout(2000)
            pg.wait_for_timeout(6000)
        if "app.kiro.dev" not in pg.url or "signin" in pg.url:
            res["situacao"], res["trecho"] = "nao_entrou", f"{pg.url[:120]} | {_texto(pg)[:200]}"
            return res
        # Settings > Account & plan: abre PELO ENDEREÇO e só lê (a página tem "Delete account": não clicar em nada)
        pg.goto(KIRO + "settings/account", wait_until="domcontentloaded", timeout=90000)
        pg.wait_for_timeout(8000)
        _recusar_cookies(pg)
        txt = _texto(pg)
        if email not in txt.lower() or "credits" not in txt.lower():
            res["situacao"], res["trecho"] = "pagina_inesperada", txt[:300]
            return res
        PRINTS.mkdir(exist_ok=True)
        pg.screenshot(path=str(PRINTS / f"{email.split('@')[0]}.png"))
        res.update(situacao="usa_kiro", **_creditos(txt))
        try:
            com_credito = float(res.get("restantes") or 0) > 0
        except ValueError:
            com_credito = False
        if deixar and com_credito:
            manter = res["janela_aberta"] = True
            _na_tela(br, pg)
        return res
    except Exception as e:  # noqa: BLE001
        res["situacao"] = f"erro {type(e).__name__}: {str(e)[:120]}"
        return res
    finally:
        # dona 23/10: "essas que não entram deixe aberto também" — só fecha conta que usa o Kiro e está sem crédito
        if deixar and not manter and res.get("situacao") != "usa_kiro" and br is not None:
            manter = res["janela_aberta"] = True
            try:
                _na_tela(br, next(x for x in br.contexts[0].pages if "kiro" in x.url or "google" in x.url))
            except Exception:  # noqa: BLE001
                pass
        if not manter:
            try:
                cofre.fechar(proc, br, email)
            except Exception:  # noqa: BLE001
                pass


def abrir_para_dona(email, p):
    """Conta SEM Kiro (dona 23/10: "as que não tiverem conta você abre e deixa aberta e me avisa"): janela NA TELA,
    parada na tela de permissão do Google ("Continuar"). Quem clica é a dona — o script não aceita nada. A janela fica
    aberta (o cofre fecha pelo uso normal depois)."""
    porta, _proc = cofre.abrir(email, visivel=True)
    br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
    pg = br.contexts[0].new_page()
    try:  # perfil que já estava aberto escondido (fora da tela): traz pra tela
        s = br.contexts[0].new_cdp_session(pg)
        jan = s.send("Browser.getWindowForTarget")
        s.send("Browser.setWindowBounds", {"windowId": jan["windowId"], "bounds": {"windowState": "normal"}})
        s.send("Browser.setWindowBounds", {"windowId": jan["windowId"],
                                           "bounds": {"left": 60, "top": 40, "width": 1280, "height": 900}})
    except Exception:  # noqa: BLE001
        pass
    pg.goto(KIRO, wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(6000)
    _recusar_cookies(pg)
    if "signin" in pg.url:
        pg.get_by_text("Google", exact=True).first.click()
        pg.wait_for_timeout(8000)
        alvo = pg.locator(f'[data-identifier="{email}"]')
        if alvo.count():
            alvo.first.click()
            pg.wait_for_timeout(6000)
    pg.bring_to_front()
    return pg.url  # sai sem fechar: a janela continua na tela


def _abrir_credito(email, p):
    """Conta com crédito: janela NA TELA na página do plano (a dona conecta no OmniRoute)."""
    porta, _ = cofre.abrir(email, visivel=True)
    br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
    pg = br.contexts[0].new_page()
    pg.goto(KIRO + "settings/account", wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(6000)
    _recusar_cookies(pg)
    _na_tela(br, pg)


def fila(maximo=5, ja_feitas=(), so_sem_kiro=False):
    """Dona 23/10: abre, no máximo `maximo` por vez, as janelas que precisam dela — sem Kiro (Continuar), não entrou e
    com crédito (conectar no OmniRoute). Janela que ela fechou = feita (anota "dona_fechou") e abre a próxima.
    Roda até a fila acabar."""
    from playwright.sync_api import sync_playwright
    reg = cofre._ler()["contas"]
    feitas = {cofre.conta(x)[0] for x in ja_feitas}

    def precisa(r):
        if so_sem_kiro:  # --so-sem-kiro: só as que a dona ainda precisa CRIAR
            return r.get("situacao") in ("sem_kiro", "nao_entrou")
        return r.get("situacao") in ("sem_kiro", "nao_entrou") or (
            r.get("situacao") == "usa_kiro" and float(r.get("restantes") or 0) > 0)
    with sync_playwright() as p:
        while True:
            d = _ler()
            for e in feitas:
                if e in d and not d[e].get("dona_fechou"):
                    d[e]["dona_fechou"] = datetime.now().isoformat(timespec="minutes")
            fila_ = [e for e, r in d.items() if precisa(r) and not r.get("dona_fechou") and e in reg]
            abertas = [e for e in fila_ if cofre._cdp_vivo(reg[e]["porta"]) or cofre.porta_aberta(reg[e]["pasta"])]
            for e in fila_:  # abriu antes e agora está fechada: a dona terminou
                if d[e].get("aberta_fila") and e not in abertas:
                    d[e]["dona_fechou"] = datetime.now().isoformat(timespec="minutes")
            _gravar(d)
            fila_ = [e for e in fila_ if not d[e].get("dona_fechou")]
            if not fila_:
                print("fila terminada")
                relatorio()
                return
            for e in [x for x in fila_ if x not in abertas][:max(0, maximo - len(abertas))]:
                if _ram_livre_gb() < RAM_MIN_GB:
                    break
                try:
                    if d[e].get("situacao") == "usa_kiro":
                        _abrir_credito(e, p)
                    else:
                        abrir_para_dona(e, p)
                    d = _ler()
                    d[e]["aberta_fila"] = datetime.now().isoformat(timespec="minutes")
                    _gravar(d)
                    print(f"aberta: {e} ({d[e].get('situacao')})", flush=True)
                except Exception as ex:  # noqa: BLE001
                    print(f"{e}: não abriu ({type(ex).__name__}: {str(ex)[:80]})", flush=True)
            time.sleep(30)


def relatorio():
    d = _ler()
    grupos = {"usa_kiro": [], "sem_kiro": [], "outros": []}
    for email, r in sorted(d.items()):
        grupos.get(r.get("situacao"), grupos["outros"]).append((email, r))
    ln = [f"# Créditos do Kiro por conta (kiro_creditos.py)", "",
          f"Atualizado {datetime.now():%d/%m %H:%M}. {len(grupos['usa_kiro'])} usam o Kiro, "
          f"{len(grupos['sem_kiro'])} nunca entraram, {len(grupos['outros'])} com outro resultado.", "",
          "## Usam o Kiro", "", "| conta | créditos | plano | renova | lido em |", "|---|---|---|---|---|"]
    janela = lambda r: " · janela aberta" if r.get("janela_aberta") else " · abrir com --abrir" if r.get("abrir_depois") else ""  # noqa: E731
    for email, r in sorted(grupos["usa_kiro"], key=lambda x: -float(x[1].get("restantes") or 0)):
        cred = (f"{r['restantes']} restantes ({r.get('usados')}/{r.get('limite')} usados)" if r.get("limite") else "")
        ln.append(f"| {email} | {cred or 'ver print em kiro_prints'}{janela(r)} | {r.get('plano', '')} | "
                  f"{r.get('renova', '')} | {r['em']} |")
    ln += ["", "## Sem conta no Kiro (o Google pede a permissão \"Continuar\": quem decide é a dona)", ""]
    ln += [f"- {e}{janela(r)}" for e, r in grupos["sem_kiro"]] or ["- nenhuma"]
    ln += ["", "## Outros resultados", ""]
    ln += [f"- {e}: {r.get('situacao')}" for e, r in grupos["outros"]] or ["- nenhum"]
    extras = sorted({x for r in d.values() for x in r.get("outras_contas_no_perfil") or []})
    ln += ["", "## Contas que aparecem nos perfis e NÃO estão no cofre (não conferidas)", ""]
    ln += [f"- {x}" for x in extras] or ["- nenhuma"]
    RELATORIO.write_text("\n".join(ln) + "\n", encoding="utf-8")
    return RELATORIO


def main(args):
    if "--relatorio" in args:
        print(relatorio())
        return
    from playwright.sync_api import sync_playwright
    if "--fila" in args:  # no máximo 5 janelas por vez; a dona fecha uma, abre a próxima
        fila(5, [a for a in args if not a.startswith("--")], so_sem_kiro="--so-sem-kiro" in args)
        return
    if "--abrir" in args:  # contas sem Kiro: janela na tela, na permissão do Google, pra dona clicar em Continuar
        with sync_playwright() as p:
            for a in [x for x in args if x != "--abrir"]:
                email = cofre.conta(a)[0]
                print(f"{email}: janela aberta na tela ({abrir_para_dona(email, p)[:80]})")
        return
    reg = cofre._ler()["contas"]
    contas_arg = [a for a in args if not a.startswith("--")]
    if contas_arg:
        alvos = [cofre.conta(a)[0] for a in contas_arg]
    else:
        alvos = [e for e, v in reg.items() if v.get("google") == "vivo" and v.get("tipo") != "instagram"]
    d = _ler()
    with sync_playwright() as p:
        for i, email in enumerate(alvos, 1):
            if cofre.em_uso(reg[email]["pasta"]) and not cofre._cdp_vivo(reg[email]["porta"]):
                print(f"[{i}/{len(alvos)}] {email}: perfil em uso por outro programa — pulada")
                continue
            deixar = "--fechar-todas" not in args and _ram_livre_gb() >= RAM_MIN_GB
            r = conferir(email, p, deixar=deixar)
            if not deixar and (r.get("situacao") == "sem_kiro" or float(r.get("restantes") or 0) > 0):
                r["abrir_depois"] = True  # RAM curta: não ficou aberta — python kiro_creditos.py --abrir <conta>
            d = _ler()
            d[email] = r
            _gravar(d)
            print(f"[{i}/{len(alvos)}] {email}: {r.get('situacao')} "
                  f"{({k: r[k] for k in ('usados', 'limite', 'restantes', 'plano') if k in r})}", flush=True)
    print(relatorio())


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main(sys.argv[1:])
