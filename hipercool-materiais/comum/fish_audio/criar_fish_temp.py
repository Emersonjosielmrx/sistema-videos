r"""criar_fish_temp.py — cria UMA conta do Fish Audio com e-mail TEMPORÁRIO real (mail.tm), CADASTRANDO PELA CASA
(o reCAPTCHA do Fish recusa cadastro por IP de datacenter — medido 19/11: "A verificação de segurança falhou"; pela
casa a nota é alta e passa). Conta de e-mail temp, sem Google, não liga família (dona 19/11 escolheu a casa).

Depois que loga, a conta já é gravada no cofre com fish_proxy = rnprmtfo-N (IP do Fish que NUNCA tocou o Kaggle, máx 2
contas por IP), e a sessão guardada. A PARTIR DAÍ a conta só fala com o Fish pelo IP fixo (fábrica/rodízio). Só o
cadastro inicial sai pela casa, uma vez.

Fluxo: cria caixa temp -> Chrome pela CASA visível -> Criar conta -> e-mail -> Continuar (reCAPTCHA) -> lê código pela
API do mail.tm (sem proxy) -> preenche código + senha -> logado -> grava no cofre no IP N + saldo. Captcha visível =
apita e espera a dona.

    python criar_fish_temp.py <N>      # cria 1 conta e guarda no IP rnprmtfo-N do Fish
"""
import json
import re
import secrets
import socket
import string
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, r"D:\logins-google")
sys.path.insert(0, r"D:\hipercool-materiais\emails_temporarios")

import cofre            # noqa: E402
import fish_audio as fa  # noqa: E402
import pool_fish        # noqa: E402
import avisar_dona      # noqa: E402
import testar_provedores as tp  # noqa: E402
import requests         # noqa: E402

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PERFIS = Path(r"D:\logins-google\cofre\perfis_fish_temp")
POOL_KAGGLE = Path(r"D:\recapd-ambientes\producao\colab\kaggle_pool.json")
LOG = AQUI / "criar_fish_temp.log"
PRINTS = Path(r"D:\tmp\fish_proton")
PRINTS.mkdir(parents=True, exist_ok=True)
MAX_POR_IP = 2
MAILTM = "https://api.mail.tm"


def log(m):
    linha = datetime.now().strftime("%H:%M:%S ") + m
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")
    print(linha, flush=True)


def ips_que_tocaram_kaggle():
    toc = set()
    toc |= {int(m) for m in re.findall(r"rnprmtfo-(\d+)", POOL_KAGGLE.read_text(encoding="utf-8"))}
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


def checar_ip(n):
    if n in ips_que_tocaram_kaggle():
        raise SystemExit(f"rnprmtfo-{n} já tocou o Kaggle — proibido")
    if f"rnprmtfo-{n}" not in pool_fish.pool_atual().values():
        raise SystemExit(f"rnprmtfo-{n} não é um IP do pool do Fish")
    if contas_no_ip(n) >= MAX_POR_IP:
        raise SystemExit(f"rnprmtfo-{n} já tem {MAX_POR_IP} contas do Fish")


def nova_caixa():
    """mail.tm direto (sem proxy — é só e-mail). Devolve (email, token)."""
    s = requests.Session()
    s.trust_env = False
    doms = s.get(f"{MAILTM}/domains", timeout=25).json()
    dom = (doms.get("hydra:member") or doms)[0]["domain"]
    nome = "".join(secrets.choice(string.ascii_lowercase) for _ in range(10))
    email, senha = f"{nome}@{dom}", "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(14))
    s.post(f"{MAILTM}/accounts", json={"address": email, "password": senha}, timeout=25).raise_for_status()
    tok = s.post(f"{MAILTM}/token", json={"address": email, "password": senha}, timeout=25).json()["token"]
    return email, tok


def ler_codigo(token, seg=240):
    """Busca o código de verificação do Fish na caixa mail.tm (lê o CORPO), sem proxy."""
    s = requests.Session()
    s.trust_env = False
    h = {"Authorization": f"Bearer {token}"}
    t0 = time.time()
    while time.time() - t0 < seg:
        try:
            r = s.get(f"{MAILTM}/messages", headers=h, timeout=25).json()
            for m in (r.get("hydra:member") or r):
                if "fish" not in json.dumps(m).lower():
                    continue
                full = s.get(f"{MAILTM}/messages/{m['id']}", headers=h, timeout=25).json()
                corpo = " ".join(str(full.get(k, "")) for k in ("subject", "intro", "text")) + " " + \
                    " ".join(full.get("html") or [])
                link = re.search(r"https://fish\.audio/[^\s\"'<>]*(verif|confirm|activate)[^\s\"'<>]*", corpo, re.I)
                cod = re.search(r"\b(\d{6})\b", corpo) or re.search(r"\bcode[^0-9A-Z]{0,20}([0-9A-Z]{6})\b", corpo, re.I)
                if link or cod:
                    return (cod.group(1) if cod else None), (link.group(0) if link else None)
        except Exception as e:  # noqa: BLE001
            log(f"ler mail.tm: {type(e).__name__}: {str(e)[:60]}")
        time.sleep(7)
    return None, None


def _porta_livre():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def _click_txt(pg, padrao, timeout=12000):
    pg.get_by_text(re.compile(padrao, re.I)).first.click(timeout=timeout)


def _digita(pg, sel, valor):
    el = pg.locator(sel).first
    el.click(timeout=12000)
    el.press("Control+A")
    el.press("Delete")
    el.type(valor, delay=45)


def _txt(pg):
    try:
        return re.sub(r"\s+", " ", pg.inner_text("body"))
    except Exception:  # noqa: BLE001
        return ""


def main(n):
    checar_ip(n)
    email, token = nova_caixa()
    senha = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12)) + "x7A"
    usuario = email.split("@")[0]
    pasta = PERFIS / usuario
    log(f"=== {email} (mail.tm) -> IP rnprmtfo-{n} (outras no IP: {contas_no_ip(n)}) | cadastro pela CASA")

    cdp = _porta_livre()
    proc = subprocess.Popen([CHROME, f"--remote-debugging-port={cdp}", f"--user-data-dir={pasta}", "--no-first-run",
                             "--no-default-browser-check", "--window-position=60,40", "--start-maximized",
                             "--disable-backgrounding-occluded-windows", "about:blank"])
    from playwright.sync_api import sync_playwright
    ok = False
    try:
        for _ in range(60):
            try:
                socket.create_connection(("127.0.0.1", cdp), timeout=1).close()
                break
            except OSError:
                time.sleep(0.5)
        with sync_playwright() as pw:
            b = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{cdp}")
            ctx = b.contexts[0]
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
            avisar_dona.na_frente(proc.pid)
            pg.goto("https://fish.audio/pt/auth/", wait_until="domcontentloaded", timeout=90000)
            time.sleep(6)
            _click_txt(pg, "Criar conta")
            time.sleep(3)
            _digita(pg, "input[type=email]", email)
            time.sleep(1)
            pg.get_by_role("button", name=re.compile("Continuar|Continue", re.I)).first.click(timeout=10000)
            log(f"{email}: enviado o e-mail no cadastro — esperando reCAPTCHA/código")
            time.sleep(10)
            if re.search(r"(?i)verifica\w+ de segurança falhou|security (check|verification) failed", _txt(pg)):
                pg.screenshot(path=str(PRINTS / f"{usuario}_recaptcha_falhou.png"))
                raise SystemExit("reCAPTCHA recusou mesmo pela casa — ver print")
            if re.search(r"(?i)não sou um robô|not a robot|verifica\w+ humana", _txt(pg)):
                avisar_dona.chamar(proc.pid, apitar=True)
                log(f">>> DONA: captcha visível no cadastro de {email} — resolva. Espero 8 min.")
                fim = time.time() + 480
                while time.time() < fim and re.search(r"(?i)robô|robot|humana", _txt(pg)):
                    time.sleep(5)
            # código do e-mail
            cod, link = ler_codigo(token, seg=200)
            if link:
                log(f"{email}: confirmando pelo link")
                pg.goto(link, wait_until="domcontentloaded", timeout=60000)
                time.sleep(6)
            elif cod:
                log(f"{email}: código {cod}")
                campos = pg.locator("input:not([type=email]):not([type=password])")
                if campos.count() >= 6:
                    for i, ch in enumerate(cod):
                        campos.nth(i).type(ch, delay=80)
                else:
                    try:
                        _digita(pg, "input:not([type=email]):not([type=password])", cod)
                        pg.keyboard.press("Enter")
                    except Exception:  # noqa: BLE001
                        pass
                time.sleep(6)
            else:
                log(f"{email}: não chegou código/link em ~3 min")
            # senha, se pedir
            try:
                ps = pg.locator("input[type=password]")
                if ps.count():
                    _digita(pg, "input[type=password]", senha)
                    time.sleep(1)
                    for nome_b in ("Criar conta", "Continuar", "Concluir", "Registar", "Sign up"):
                        try:
                            pg.get_by_role("button", name=re.compile(nome_b, re.I)).first.click(timeout=4000)
                            break
                        except Exception:  # noqa: BLE001
                            pass
                    time.sleep(8)
            except Exception:  # noqa: BLE001
                pass
            # logado?
            tok_fish = None
            ws = None
            for x in ctx.pages:
                try:
                    if "fish.audio" in x.url:
                        tok_fish = x.evaluate("() => localStorage.getItem('token') || ''") or None
                        ws = x.evaluate("() => localStorage.getItem('active_workspace_id') || ''") or None
                        if tok_fish:
                            break
                except Exception:  # noqa: BLE001
                    pass
            pg.screenshot(path=str(PRINTS / f"{usuario}_fim.png"))
            if tok_fish:
                # agora sim entra no cofre, no IP fixo do Fish
                cofre.registrar(email, pasta=pasta,
                                usos={"fish_audio": "conta e-mail temp só do Fish — dona 19/11"},
                                fish_proxy=f"rnprmtfo-{n}", tipo_login="email_temp", senha_fish=senha,
                                email_token=token, cadastro_saida="casa",
                                _obs="e-mail temporário (mail.tm). Cadastro uma vez pela casa; depois só pelo IP do Fish.")
                import sessoes_fish
                sessoes_fish.gravar(email, tok_fish, ws)
                try:
                    r = sessoes_fish.saldo(email)
                except Exception as ex:  # noqa: BLE001
                    r = f"saldo falhou ({type(ex).__name__})"
                cofre._marcar(email, fish_logado=time.strftime("%Y-%m-%dT%H:%M"))
                ok = True
                log(f"{email}: LOGADO ✔ no IP rnprmtfo-{n} -> saldo {r}")
            else:
                log(f"{email}: não logou (ver print {usuario}_fim.png)")
    finally:
        try:
            proc.terminate()
        except Exception:  # noqa: BLE001
            pass
    return ok


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    main(int(sys.argv[1]))
