r"""criar_fish_proton.py — cria UMA conta do Fish Audio com uma caixa Proton do criador (sem conta Google), dividindo um
IP rnprmtfo-N do Fish. Dona 19/11: "pode repetir algum IP contanto que ele não seja usado no Kaggle" e "usar 5 dos 8"
e-mails Proton livres (nunca viraram conta no Kaggle). "Sim, 2 por IP no máximo".

Regras conferidas ANTES de abrir qualquer coisa:
  - o e-mail NÃO é de conta viva do Kaggle (cruzaria pelo e-mail);
  - o IP N está no pool do Fish e NUNCA tocou o Kaggle (pool, reservas/testes do criador, kaggle_proxy*, conflitos);
  - no máximo 2 contas do Fish por IP.

A conta entra no cofre como conta normal (cofre.registrar: porta e pasta próprias, fish_proxy = rnprmtfo-N,
tipo_login = "proton"), então a fábrica, o rodízio e as travas tratam igual às do Google. A dona faz o cadastro na
janela (o script mostra e-mail e senha); a caixa Proton fica aberta na 2ª aba do MESMO Chrome/IP para ela pegar o
código. Logou = token salvo da janela + saldo (sessoes_fish).

    python criar_fish_proton.py <email@proton.me> <N>
"""
import json
import re
import secrets
import string
import sys
import time
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, r"D:\logins-google")
sys.path.insert(0, r"D:\criador-contas-kaggle")

import cofre            # noqa: E402
import fish_audio as fa  # noqa: E402
import pool_fish        # noqa: E402
import avisar_dona      # noqa: E402

PERFIS = Path(r"D:\logins-google\cofre\perfis_fish_proton")
CAIXAS = Path(r"D:\criador-contas-kaggle\caixas_email.json")
POOL_KAGGLE = Path(r"D:\recapd-ambientes\producao\colab\kaggle_pool.json")
LOG = AQUI / "criar_fish_proton.log"
PRINTS = Path(r"D:\tmp\fish_proton")
PRINTS.mkdir(parents=True, exist_ok=True)
MAX_POR_IP = 2


def log(m):
    linha = datetime.now().strftime("%H:%M:%S ") + m
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")
    print(linha, flush=True)


def ips_que_tocaram_kaggle():
    toc = set()
    try:
        toc |= {int(m) for m in re.findall(r"rnprmtfo-(\d+)", POOL_KAGGLE.read_text(encoding="utf-8"))}
    except OSError:
        raise SystemExit("não consegui ler o kaggle_pool.json — sem conferir não crio")
    for a in Path(r"D:\criador-contas-kaggle").glob("*.json"):
        t = a.read_text(encoding="utf-8", errors="ignore")
        toc |= {int(m) for m in re.findall(r'"p(\d+)"', t)} | {int(m) for m in re.findall(r"rnprmtfo-(\d+)", t)}
    for e in cofre._ler().get("contas", {}).values():
        for k in ("kaggle_proxy", "kaggle_proxy_antigo", "fish_proxy_conflito"):
            m = re.match(r"rnprmtfo-(\d+)", str(e.get(k) or ""))
            if m:
                toc.add(int(m.group(1)))
    return toc


def contas_no_ip(n, sem=None):
    return sum(1 for em, e in cofre._ler().get("contas", {}).items()
               if em != sem and str(e.get("fish_proxy") or "") == f"rnprmtfo-{n}")


def checar(email, n):
    pool = json.loads(POOL_KAGGLE.read_text(encoding="utf-8"))["contas"]
    vivos = {str(c.get("email") or c.get("cofre") or "").lower() for c in pool if not c.get("banida")}
    if email in vivos:
        raise SystemExit(f"{email} é e-mail de conta VIVA do Kaggle — proibido (cruza pelo e-mail)")
    if n in ips_que_tocaram_kaggle():
        raise SystemExit(f"rnprmtfo-{n} já tocou o Kaggle — proibido")
    if f"rnprmtfo-{n}" not in pool_fish.pool_atual().values():
        raise SystemExit(f"rnprmtfo-{n} não é um IP do pool do Fish")
    if contas_no_ip(n, sem=email) >= MAX_POR_IP:
        raise SystemExit(f"rnprmtfo-{n} já tem {MAX_POR_IP} contas do Fish")
    caixas = json.loads(CAIXAS.read_text(encoding="utf-8"))
    lista = caixas if isinstance(caixas, list) else list(caixas.values())
    cx = next((c for c in lista if str(c.get("email") or "").lower() == email), None)
    if not cx or not cx.get("senha"):
        raise SystemExit(f"{email} não está em caixas_email.json com senha")
    return cx["senha"]


def _senha_fish():
    base = string.ascii_letters + string.digits
    return "".join(secrets.choice(base) for _ in range(12)) + "!7a"


def _token(ctx):
    for x in ctx.pages:
        try:
            if "fish.audio" in x.url:
                t = x.evaluate("() => localStorage.getItem('token') || ''")
                if t and len(t) > 10:
                    w = x.evaluate("() => localStorage.getItem('active_workspace_id') || ''") or None
                    return t, w
        except Exception:  # noqa: BLE001
            pass
    return None, None


def main(email, n):
    email = email.lower()
    senha_proton = checar(email, n)
    usuario = email.split("@")[0]
    e = cofre._ler()["contas"].get(email) or {}
    senha_fish = e.get("senha_fish") or _senha_fish()
    # grava ANTES de usar (regra do criador: senha gravada antes de enviar). Conta normal do cofre: porta e pasta
    # próprias; a fábrica/rodízio passam a enxergar como qualquer conta do Fish.
    cofre.registrar(email, pasta=PERFIS / usuario, usos={"fish_audio": "conta Proton só do Fish — dona 19/11"},
                    fish_proxy=f"rnprmtfo-{n}", tipo_login="proton", senha_fish=senha_fish,
                    _obs="caixa Proton do criador (nunca virou Kaggle). Login no Fish por E-MAIL, não Google.")
    log(f"=== {email} pelo rnprmtfo-{n} (outras contas no IP: {contas_no_ip(n, sem=email)})")

    porta_px = fa._subir_ponte(n)
    porta, proc = cofre.abrir(email, visivel=True, extra=(f"--proxy-server=127.0.0.1:{porta_px}",
                                                          "--proxy-bypass-list=<-loopback>"))
    from playwright.sync_api import sync_playwright
    ok = False
    try:
        with sync_playwright() as pw:
            b = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
            ctx = b.contexts[0]
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
            pg.goto("https://ipv4.webshare.io/", timeout=40000)
            ip = pg.inner_text("body").strip()
            if ip.startswith("191.36."):
                raise SystemExit("saída é a CASA — parei")
            log(f"{email}: saída {ip}")
            tok, ws = _token(ctx)
            if not tok:
                cx = ctx.new_page()   # 2ª aba: caixa Proton pelo MESMO Chrome/IP
                try:
                    import criar_conta_proton as ccp
                    aberta = ccp.entrar_caixa(cx, email, senha_proton)
                    log(f"{email}: caixa Proton {'aberta na 2ª aba' if aberta else 'NÃO abriu (entrar à mão)'}")
                except Exception as ex:  # noqa: BLE001
                    log(f"{email}: caixa Proton falhou ({type(ex).__name__}) — entrar à mão")
                pg.bring_to_front()
                pg.goto("https://fish.audio/pt/", wait_until="domcontentloaded", timeout=90000)
                time.sleep(4)
                pid = proc.pid if proc else None
                avisar_dona.chamar(pid, apitar=True)
                log(f">>> DONA: Fish -> 'Cadastre-se Grátis' -> E-MAIL (não Google): {email} | senha: {senha_fish} "
                    f"| código na 2ª aba (Proton). Espero 15 min.")
                fim = time.time() + 900
                prox = time.time() + 60
                while time.time() < fim:
                    time.sleep(4)
                    if not cofre._cdp_vivo(porta):
                        log(f"{email}: a janela fechou — parei")
                        break
                    tok, ws = _token(ctx)
                    if tok:
                        break
                    if time.time() >= prox:
                        if not avisar_dona.em_foco(pid):
                            avisar_dona.na_frente(pid)
                        prox = time.time() + 60
            if tok:
                import sessoes_fish
                sessoes_fish.gravar(email, tok, ws)
                try:
                    r = sessoes_fish.saldo(email)
                except Exception as ex:  # noqa: BLE001
                    r = f"saldo falhou ({type(ex).__name__})"
                cofre._marcar(email, fish_logado=time.strftime("%Y-%m-%dT%H:%M"))
                ok = True
                log(f"{email}: LOGADO ✔ no rodízio -> saldo {r}")
            try:
                pg.screenshot(path=str(PRINTS / f"{usuario}_fim.png"))
            except Exception:  # noqa: BLE001
                pass
    finally:
        try:
            if proc:
                cofre.fechar(proc, nome=email)
            else:
                cofre._fechar_porta(porta)
        except Exception:  # noqa: BLE001
            pass
    if not ok:
        log(f"{email}: não ficou pronta")
    return ok


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1], int(sys.argv[2]))
