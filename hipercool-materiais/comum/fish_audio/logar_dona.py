r"""logar_dona.py — loga no Fish as contas do pool que FALTAM, UMA por vez, com a dona na frente da tela.

Por que à mão: o login por script trava sempre no mesmo ponto (verificação de robô depois do "Continue" do Google).
Regra da casa: captcha em conta nova = PARAR e deixar a dona resolver, nunca contornar. Então este script só prepara
o caminho e chama a dona:
  - abre a conta pela SAÍDA FIXA dela (ponte do IP rnprmtfo-N — nunca a casa);
  - janela VISÍVEL, MAXIMIZADA e SEMPRE NO TOPO (HWND_TOPMOST), com APITO uma vez quando precisa dela;
  - tenta sozinho o clique no Google; se não logar, espera a dona logar naquela janela (sem apitar de novo);
  - assim que a billing mostra "My Team" + créditos, registra a conta no rodízio (sessão + saldo) e vai para a próxima.

Não briga com narração em andamento: pega a trava do fish_lote por conta.

    python logar_dona.py                 # todas as que faltam, uma por vez
    python logar_dona.py <email>         # só uma conta
    python logar_dona.py --espera 420    # segundos que espera a dona por conta (padrão 360)

Log: logar_dona.log
"""
import re
import sys
import time
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, r"D:\logins-google")

import cofre            # noqa: E402
import fish_audio as fa  # noqa: E402
import pool_fish        # noqa: E402
import creditos         # noqa: E402
import avisar_dona      # noqa: E402

LOG = AQUI / "logar_dona.log"
PRINTS = Path(r"D:\tmp\fish_login")
PRINTS.mkdir(parents=True, exist_ok=True)

# frases que só aparecem no TEXTO VISÍVEL quando há verificação de robô de verdade (no HTML o script do reCAPTCHA
# sempre está presente — procurar lá dá falso alarme)
VERIF = ("não sou um robô", "nao sou um robo", "i'm not a robot", "verify you are human", "verifique se você é humano",
         "unusual activity", "atividade incomum", "confirme que é você", "verify it's you", "confirme sua identidade")


def log(m):
    linha = datetime.now().strftime("%H:%M:%S ") + m
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")
    print(linha, flush=True)


def _pid_do_perfil(pasta):
    """PID do Chrome PAI (o que tem a janela) cuja --user-data-dir é esta pasta. Serve quando a conta já estava
    aberta (cofre.abrir devolve proc=None) e precisamos trazer a janela à frente mesmo assim."""
    try:
        import subprocess
        alvo = str(pasta).lower().rstrip("\\/")
        ps = ("Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | "
              "Where-Object { $_.CommandLine -and ($_.CommandLine -notlike '*--type=*') } | "
              "ForEach-Object { \"$($_.ProcessId)|$($_.CommandLine)\" }")
        out = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True,
                             timeout=25, encoding="utf-8", errors="replace",
                             creationflags=0x08000000).stdout
        for linha in out.splitlines():
            if "|" not in linha:
                continue
            pid_s, cmd = linha.split("|", 1)
            if f"--user-data-dir={alvo}".lower() in cmd.lower().replace('"', ""):
                return int(pid_s.strip())
    except Exception:  # noqa: BLE001
        pass
    return None


def _esta_logado(pg):
    """Confiável: a página de cobrança só mostra 'My Team' + 'restantes' para quem está logado."""
    try:
        pg.goto("https://fish.audio/pt/app/billing/", wait_until="domcontentloaded", timeout=60000)
        time.sleep(6)
        t = pg.inner_text("body")
        return "My Team" in t and "restantes" in t
    except Exception:  # noqa: BLE001
        return False


def _texto_visivel(pg):
    try:
        return pg.inner_text("body").lower()
    except Exception:  # noqa: BLE001
        return ""


def _token_leve(ctx):
    """Login SEM atrapalhar: lê localStorage.token numa aba do fish.audio, sem navegar nada. True = logado."""
    for x in ctx.pages:
        try:
            if "fish.audio" in x.url:
                tok = x.evaluate("() => localStorage.getItem('token') || ''")
                if tok and len(tok) > 10:
                    return tok
        except Exception:  # noqa: BLE001
            pass
    return None


def _guardar_token(email, ctx):
    """19/11: salva o Bearer DIRETO da janela logada (antes de fechar). O cofre fecha o Chrome com taskkill /F e o
    login às vezes não chega ao disco — reabrir pela fábrica dava 'deslogada' (fabricadeautomacoesia, mentoriaiapro).
    Com o token salvo, sessoes_fish.saldo lê o saldo por HTTP pelo IP da conta (workspace via /team/context)."""
    tok = _token_leve(ctx)
    if not tok:
        return None
    ws = None
    for x in ctx.pages:
        try:
            if "fish.audio" in x.url:
                ws = x.evaluate("() => localStorage.getItem('active_workspace_id') || ''") or None
                break
        except Exception:  # noqa: BLE001
            pass
    try:
        import sessoes_fish
        sessoes_fish.gravar(email, tok, ws)
        r = sessoes_fish.saldo(email)
        return r
    except Exception as ex:  # noqa: BLE001
        log(f"{email}: token salvo, saldo falhou ({type(ex).__name__}: {str(ex)[:100]})")
        return None


def _tentar_google(pg, ctx, email):
    """Repete o clique que funcionou nas 2 primeiras contas: mouse no centro do ícone do Google. Não garante nada —
    se travar na verificação, a dona assume."""
    try:
        pg.goto("https://fish.audio/pt/", wait_until="domcontentloaded", timeout=90000)
        time.sleep(6)
        pg.keyboard.press("Escape")
        time.sleep(1)
        try:
            pg.get_by_role("link", name=re.compile("Cadastre-se|Inscrever|Iniciar sess", re.I)).first.click(timeout=4000)
        except Exception:  # noqa: BLE001
            pg.mouse.click(1075, 68)
        time.sleep(4)
        cx, cy = 772, 598
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
                    g = min((c[1] for c in linha), key=lambda b: b["x"])
                    cx, cy = g["x"] + g["width"] / 2, g["y"] + g["height"] / 2
                    break
        except Exception:  # noqa: BLE001
            pass
        pg.mouse.click(cx, cy)
        time.sleep(6)
        # se a janela do Google abriu e lista a conta, tenta escolher + Continuar (ajuda quando NÃO há verificação)
        g = next((x for x in ctx.pages if "accounts.google" in x.url), pg)
        try:
            g.get_by_text(email, exact=False).first.click(timeout=5000)
            time.sleep(4)
        except Exception:  # noqa: BLE001
            pass
        for nome in ("Continue", "Continuar", "Allow", "Permitir"):
            try:
                g.get_by_role("button", name=re.compile(nome, re.I)).first.click(timeout=3000)
                break
            except Exception:  # noqa: BLE001
                pass
        time.sleep(6)
    except Exception:  # noqa: BLE001
        pass


def uma(email, espera_s=360):
    email = email.lower()
    _, e = cofre.conta(email)
    m = re.match(r"rnprmtfo-(\d+)", str(e.get("fish_proxy") or ""))
    if not m:
        log(f"{email}: SEM IP no pool — pulei")
        return False
    fa.checar_conta(email)  # recusa Kaggle / fora do pool
    # 19/11: conta já aberta por OUTRO projeto (vigia_ggmax, medir_tiktok...) sem a ponte do IP do Fish = pular.
    # Abrir por cima não sai pelo IP dela e a fábrica recusa no registro; fechar quebraria o outro projeto.
    if cofre._cdp_vivo(e["porta"]):
        pid0 = _pid_do_perfil(e.get("pasta"))
        cmd = ""
        try:
            import subprocess
            cmd = subprocess.run(["powershell", "-NoProfile", "-Command",
                                  f"(Get-CimInstance Win32_Process -Filter 'ProcessId={pid0}').CommandLine"],
                                 capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20,
                                 creationflags=0x08000000).stdout if pid0 else ""
        except Exception:  # noqa: BLE001
            pass
        if f"127.0.0.1:{18500 + int(m.group(1))}" not in cmd:
            log(f"{email}: Chrome aberto por OUTRO projeto sem o IP do Fish — pulei (logar quando ele fechar)")
            return False
    porta_proxy = fa._subir_ponte(int(m.group(1)))
    porta, proc = cofre.abrir(email, visivel=True, extra=(f"--proxy-server=127.0.0.1:{porta_proxy}",))
    pid = proc.pid if proc else _pid_do_perfil(e.get("pasta"))  # conta já aberta: acha o PID pela pasta do perfil
    pref = email.split("@")[0]
    logou = False
    from playwright.sync_api import sync_playwright
    try:
        with sync_playwright() as p:
            b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
            ctx = b.contexts[0]
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
            pg.set_viewport_size({"width": 1280, "height": 900})
            avisar_dona.na_frente(pid)  # janela à frente logo ao abrir (sem apito ainda)

            if _esta_logado(pg):
                log(f"{email}: JÁ LOGADO")
                r = _guardar_token(email, ctx)
                if r:
                    log(f"{email}: no rodízio -> saldo {r} (token da janela)")
                else:
                    logou = True
                return True

            _tentar_google(pg, ctx, email)
            pg_fish = next((x for x in ctx.pages if "fish.audio" in x.url), pg)
            if _esta_logado(pg_fish):
                log(f"{email}: LOGADO sozinho ✔")
                r = _guardar_token(email, ctx)
                if r:
                    log(f"{email}: no rodízio -> saldo {r} (token da janela)")
                else:
                    logou = True
                return True

            # precisa da dona: traz a janela à frente + APITA UMA VEZ, e espera ela logar
            avisar_dona.chamar(pid, apitar=True)
            verif = any(k in _texto_visivel(pg_fish) for k in VERIF)
            try:
                pg_fish.screenshot(path=str(PRINTS / f"{pref}_DONA.png"))
            except Exception:  # noqa: BLE001
                pass
            log(f">>> DONA: logar {email} na janela em destaque "
                f"({'verificação de robô — resolva e entre com o Google' if verif else 'entre com o Google'}). "
                f"Espero {espera_s // 60} min.")

            fim = time.time() + espera_s
            prox_reforco = time.time() + 60  # reforço gentil, raro — não roubar o foco enquanto a dona digita
            while time.time() < fim:
                time.sleep(4)
                # 19/11 (emersongencshin): a janela fechou e a fila esperou os 15 min à toa
                if not cofre._cdp_vivo(porta):
                    log(f"{email}: a janela fechou — pulei (volta na próxima rodada)")
                    return False
                # checa login SEM navegar/atrapalhar: lê o localStorage.token da aba do Fish
                tok_visto = _token_leve(ctx)
                if tok_visto:
                    cofre._marcar(email, fish_logado=time.strftime("%Y-%m-%dT%H:%M"))
                    log(f"{email}: LOGADO ✔ (dona)")
                    # 19/11 (revolutionemerson2): o token sumiu 3 s depois de visto. Grava NA HORA o que foi visto;
                    # o workspace sai do /team/context se faltar.
                    try:
                        import sessoes_fish
                        sessoes_fish.gravar(email, tok_visto, None)
                    except Exception:  # noqa: BLE001
                        pass
                    r = _guardar_token(email, ctx)
                    if not r:
                        try:
                            r = sessoes_fish.saldo(email)
                        except Exception as ex:  # noqa: BLE001
                            log(f"{email}: saldo pelo token visto falhou ({type(ex).__name__}: {str(ex)[:100]})")
                    if r:
                        log(f"{email}: no rodízio -> saldo {r} (token da janela)")
                    else:
                        logou = True  # sem token direto: tenta pela fábrica depois de fechar
                    return True
                # só re-traz à frente se a janela NÃO estiver em foco, no máximo a cada 60 s, sem apito
                if time.time() >= prox_reforco:
                    if not avisar_dona.em_foco(pid):
                        avisar_dona.na_frente(pid)
                    prox_reforco = time.time() + 60
            try:
                pg_fish = next((x for x in ctx.pages if "fish.audio" in x.url), pg_fish)
                pg_fish.screenshot(path=str(PRINTS / f"{pref}_fim.png"))
            except Exception:  # noqa: BLE001
                pass
            log(f"{email}: não logou no tempo — pulei (print {PRINTS / (pref + '_fim.png')})")
            return False
    finally:
        # fecha o Chrome desta conta SEMPRE (grava cookies do login). Mesmo com proc=None (a janela foi aberta por
        # fora, sem a ponte do IP), precisa fechar: a fábrica se recusa a reabrir por cima dela para registrar.
        try:
            if proc:
                cofre.fechar(proc, nome=email)
            else:
                cofre._fechar_porta(porta)
        except Exception:  # noqa: BLE001
            pass
        if logou:
            # 19/11: esperar o Chrome largar a pasta de verdade (2 s fixos não bastavam: a fábrica dava "pasta já
            # aberta em outro Chrome" e o registro falhava)
            for _ in range(30):
                if not cofre._cdp_vivo(porta) and not cofre.porta_aberta(Path(e["pasta"])):
                    break
                time.sleep(1)
            time.sleep(3)
            _registrar(email)  # agora a fábrica reabre pela ponte do IP e grava token + saldo


def _registrar(email):
    """Depois de logado: grava a sessão (token) e lê o saldo, para a conta entrar no rodízio por crédito."""
    try:
        import sessoes_fish
        r = sessoes_fish.registrar_conta(email)
        log(f"{email}: no rodízio -> saldo {r}")
    except Exception as ex:  # noqa: BLE001
        # 19/11: NÃO marcar logada — a conta deslogada entrava no rodízio e a produção tentaria usar
        creditos.marcar(email, logado=False, erro=f"registrar falhou: {str(ex)[:100]}")
        log(f"{email}: NÃO FICOU PRONTA — registrar falhou ({type(ex).__name__}: {str(ex)[:140]}) "
            f"— relogar: python logar_dona.py {email}")


def faltam():
    reg = creditos.carregar()
    try:
        import sessoes_fish
        ses = sessoes_fish.carregar()
    except Exception:  # noqa: BLE001
        ses = {}
    out = []
    PULAR = {"revolutionemerson3@gmail.com", "comoseriasecomia@gmail.com"}  # dona 19/11: "pule essa"
    for e in sorted(pool_fish.pool_atual()):
        if e in PULAR:
            continue
        tem_sessao = bool((ses.get(e) or {}).get("token")) and not (ses.get(e) or {}).get("morta")
        if (reg.get(e) or {}).get("logado") and tem_sessao:
            continue
        out.append(e)
    return out


def main():
    espera = 360
    argv = sys.argv[1:]
    args = []
    i = 0
    while i < len(argv):
        if argv[i] == "--espera":
            espera = int(argv[i + 1]) if i + 1 < len(argv) else espera
            i += 2
            continue
        if argv[i].startswith("--"):
            i += 1
            continue
        args.append(argv[i])
        i += 1
    if args:
        alvo = [args[0].lower()]
    else:
        alvo = faltam()
    if not alvo:
        log("nada a logar — todas as contas do pool já têm login e sessão")
        return
    log(f"=== logar_dona: {len(alvo)} conta(s) a logar (espera {espera}s por conta) ===")
    ok = 0
    # 19/11: SEM a trava do fish_lote. Ela serve para 2 narrações não usarem a mesma conta; o login só mexe em contas
    # que ainda não estão no rodízio (a produção não usa). Com ela, a fila esperava 10 min por Short em andamento.
    travou = False
    try:
        for i, email in enumerate(alvo, 1):
            log(f"--- [{i}/{len(alvo)}] {email} ---")
            try:
                if uma(email, espera_s=espera):
                    ok += 1
            except SystemExit as ex:
                log(f"{email}: recusada ({ex})")
            except Exception as ex:  # noqa: BLE001
                log(f"{email}: erro {type(ex).__name__}: {str(ex)[:160]}")
            time.sleep(4)
    finally:
        if travou:
            try:
                import fish_lote
                fish_lote._soltar()
            except Exception:  # noqa: BLE001
                pass
    log(f"=== fim: {ok}/{len(alvo)} logadas ===")


if __name__ == "__main__":
    main()
