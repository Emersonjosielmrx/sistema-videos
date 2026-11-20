r"""criar_fish_mao.py — cria UMA conta do Fish Audio com a DONA fazendo o cadastro à mão (o reCAPTCHA do cadastro só
passa em navegador de verdade; por script é inviável — medido 19/11). O script prepara tudo, avisa com APITO + janela
na frente (igual ao criador do Kaggle), LÊ o código do e-mail e mostra pra dona, e quando ela loga põe no rodízio.

Dona 19/11: "faz o captcha manual, com aviso sonoro na hora igual ao do Kaggle". Cadastro pela CASA (reCAPTCHA nota
alta; conta de e-mail temp sem Google não liga família). Depois de logada, a conta sai pelo IP fixo rnprmtfo-N do Fish
(nunca tocou o Kaggle, máx 2 por IP).

O QUE A DONA FAZ (só isso):
  1. Na janela do Fish: clicar "Cadastre-se Grátis" / "Criar conta" -> digitar o E-MAIL que o script mostrar ->
     Continuar -> (resolver o "não sou um robô" se aparecer) -> digitar o CÓDIGO que o script mostrar -> senha que o
     script mostrar -> concluir.
  O script repete o apito a cada 30 s enquanto ela não terminar, e fecha tudo sozinho quando loga.

    python criar_fish_mao.py <N>          # cria 1 conta no IP rnprmtfo-N do Fish
"""
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

import requests         # noqa: E402
import cofre            # noqa: E402
import fish_audio as fa  # noqa: E402
import pool_fish        # noqa: E402
import avisar_dona      # noqa: E402

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PERFIS = Path(r"D:\logins-google\cofre\perfis_fish_temp")
POOL_KAGGLE = Path(r"D:\recapd-ambientes\producao\colab\kaggle_pool.json")
LOG = AQUI / "criar_fish_mao.log"
MAILTM = "https://api.mail.tm"
MAX_POR_IP = 2
REAPITO_S = 30


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


def contas_no_ip(n):
    return sum(1 for e in cofre._ler().get("contas", {}).values()
               if str(e.get("fish_proxy") or "") == f"rnprmtfo-{n}")


def checar_ip(n):
    if n in ips_que_tocaram_kaggle():
        raise SystemExit(f"rnprmtfo-{n} já tocou o Kaggle — proibido")
    if f"rnprmtfo-{n}" not in pool_fish.pool_atual().values():
        raise SystemExit(f"rnprmtfo-{n} não é um IP do pool do Fish")
    if contas_no_ip(n) >= MAX_POR_IP:
        raise SystemExit(f"rnprmtfo-{n} já tem {MAX_POR_IP} contas do Fish")


def nova_caixa():
    s = requests.Session()
    s.trust_env = False
    dom = (s.get(f"{MAILTM}/domains", timeout=25).json().get("hydra:member"))[0]["domain"]
    nome = "".join(secrets.choice(string.ascii_lowercase) for _ in range(10))
    email = f"{nome}@{dom}"
    senha_cx = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(14))
    s.post(f"{MAILTM}/accounts", json={"address": email, "password": senha_cx}, timeout=25).raise_for_status()
    tok = s.post(f"{MAILTM}/token", json={"address": email, "password": senha_cx}, timeout=25).json()["token"]
    return email, tok


def codigo_na_caixa(token):
    """Último código do Fish na caixa (ou None). Lê a cada chamada; o laço principal controla o ritmo (sem 429)."""
    s = requests.Session()
    s.trust_env = False
    h = {"Authorization": f"Bearer {token}"}
    try:
        r = s.get(f"{MAILTM}/messages", headers=h, timeout=20).json()
        for m in (r.get("hydra:member") or r):
            if "fish" not in __import__("json").dumps(m).lower():
                continue
            full = s.get(f"{MAILTM}/messages/{m['id']}", headers=h, timeout=20).json()
            corpo = " ".join(str(full.get(k, "")) for k in ("subject", "intro", "text")) + " " + \
                " ".join(full.get("html") or [])
            cod = re.search(r"\b(\d{6})\b", corpo) or re.search(r"\bcode[^0-9A-Za-z]{0,20}([0-9A-Z]{6})\b", corpo, re.I)
            if cod:
                return cod.group(1)
    except Exception:  # noqa: BLE001
        pass
    return None


def _token_fish(ctx):
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


def main(n):
    checar_ip(n)
    email, token_cx = nova_caixa()
    senha = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10)) + "x7A"
    usuario = email.split("@")[0]
    pasta = PERFIS / usuario

    print("\n" + "=" * 64)
    print("  CONTA NOVA DO FISH — a dona faz o cadastro à mão na janela")
    print(f"  E-MAIL:  {email}")
    print(f"  SENHA:   {senha}")
    print(f"  IP:      rnprmtfo-{n}   (outras contas no IP: {contas_no_ip(n)})")
    print("=" * 64 + "\n", flush=True)
    log(f"=== {email} | IP rnprmtfo-{n} | cadastro à MÃO pela casa")

    cdp = socket.socket()
    cdp.bind(("127.0.0.1", 0))
    porta_cdp = cdp.getsockname()[1]
    cdp.close()
    proc = subprocess.Popen([CHROME, f"--remote-debugging-port={porta_cdp}", f"--user-data-dir={pasta}",
                             "--no-first-run", "--no-default-browser-check", "--window-position=60,40",
                             "--start-maximized", "--disable-backgrounding-occluded-windows", "about:blank"])
    from playwright.sync_api import sync_playwright
    ok = False
    try:
        for _ in range(80):
            try:
                socket.create_connection(("127.0.0.1", porta_cdp), timeout=1).close()
                break
            except OSError:
                time.sleep(0.5)
        with sync_playwright() as pw:
            b = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta_cdp}")
            ctx = b.contexts[0]
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
            try:
                pg.goto("https://fish.audio/pt/auth/signup/", wait_until="commit", timeout=120000)
            except Exception:  # noqa: BLE001
                pass
            time.sleep(10)

            def body(pg_):
                try:
                    return re.sub(r"\s+", " ", pg_.evaluate("()=>document.body?document.body.innerText:''"))
                except Exception:  # noqa: BLE001
                    return ""

            def js_set(sel, val):
                return pg.evaluate("""([sel,val])=>{ const set=(el,v)=>{const d=Object.getOwnPropertyDescriptor(
                  window.HTMLInputElement.prototype,'value').set; d.call(el,v); el.dispatchEvent(new Event('input',{bubbles:true}));
                  el.dispatchEvent(new Event('change',{bubbles:true}));}; const el=document.querySelector(sel);
                  if(!el) return false; el.focus(); set(el,val); return true; }""", [sel, val])

            def js_click(txt):
                return pg.evaluate("""(txt)=>{ const b=[...document.querySelectorAll('button')].find(
                  x=>new RegExp(txt,'i').test(x.innerText)); if(b){b.click(); return true;} return false; }""", txt)

            # EU faço: Criar conta -> e-mail -> Continuar
            js_click("criar conta|criar uma conta")
            time.sleep(3)
            js_set("input[type=email]", email)
            time.sleep(1)
            log(f"{email}: preenchi o e-mail, clicando Continuar")
            js_click("continuar|continue")
            time.sleep(8)

            # Se o reCAPTCHA reprovar, avisa a dona UMA vez e espera ela resolver na janela
            avisou = False
            fim = time.time() + 1800
            cod_mostrado = None
            codigo_pedido = False
            while time.time() < fim:
                time.sleep(5)
                if not cofre._cdp_vivo(porta_cdp):
                    log(f"{email}: a janela fechou — parei")
                    break
                tok, ws = _token_fish(ctx)
                if tok:
                    ok = True
                    break
                txt = body(pg).lower()
                # captcha / verificação falhou -> APITO UMA VEZ + janela na frente, espera a dona
                if any(k in txt for k in ("verificação de segurança falhou", "não sou um robô", "nao sou um robo",
                                          "not a robot", "verificação humana", "não foi possível conectar")):
                    if not avisou:
                        avisar_dona.na_frente(proc.pid)
                        avisar_dona.apito()
                        log(f">>> DONA: resolva o captcha/verificação na janela (ou clique Continuar de novo). Eu sigo depois.")
                        avisou = True
                    # a dona pode ter clicado Continuar de novo; tento reenviar o Continuar a cada 20 s sem apitar
                    continue
                # tela do código: leio da caixa e PREENCHO eu mesmo
                if any(k in txt for k in ("código", "code", "verif")) or codigo_pedido:
                    codigo_pedido = True
                    cod = codigo_na_caixa(token_cx)
                    if cod and cod != cod_mostrado:
                        cod_mostrado = cod
                        # preenche caixas de dígito OU um input único
                        feito = pg.evaluate("""(cod)=>{ const ins=[...document.querySelectorAll(
                          'input:not([type=email]):not([type=password])')]; const dig=ins.filter(i=>
                          i.maxLength===1 || /otp|code|digit/i.test(i.name+i.id+i.className));
                          const set=(el,v)=>{const d=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
                          d.call(el,v); el.dispatchEvent(new Event('input',{bubbles:true}));};
                          if(dig.length>=6){ for(let i=0;i<6;i++){ dig[i].focus(); set(dig[i],cod[i]); } return 'caixas'; }
                          if(ins.length){ ins[0].focus(); set(ins[0],cod); return 'input'; } return 'sem campo'; }""", cod)
                        log(f"{email}: código {cod} preenchido ({feito})")
                        time.sleep(2)
                        # senha, se houver
                        if pg.evaluate("()=>!!document.querySelector('input[type=password]')"):
                            js_set("input[type=password]", senha)
                            time.sleep(1)
                        for b in ("continuar", "criar conta", "concluir", "confirmar", "verificar", "sign up"):
                            if js_click(b):
                                break
                        time.sleep(6)
            tok, ws = _token_fish(ctx) if not ok else (None, None)
            if ok or tok:
                if not ok:
                    ok = True
                tok2, ws2 = _token_fish(ctx)
                cofre.registrar(email, pasta=pasta, usos={"fish_audio": "conta e-mail temp só do Fish — dona 19/11"},
                                fish_proxy=f"rnprmtfo-{n}", tipo_login="email_temp", senha_fish=senha,
                                email_token=token_cx, cadastro_saida="casa",
                                _obs="e-mail temporário (mail.tm). Cadastro à mão pela casa; depois só pelo IP do Fish.")
                import sessoes_fish
                sessoes_fish.gravar(email, tok2, ws2)
                try:
                    r = sessoes_fish.saldo(email)
                except Exception as ex:  # noqa: BLE001
                    r = f"saldo falhou ({type(ex).__name__})"
                cofre._marcar(email, fish_logado=time.strftime("%Y-%m-%dT%H:%M"))
                log(f"{email}: LOGADO ✔ no IP rnprmtfo-{n} -> saldo {r}")
    finally:
        try:
            if cofre._cdp_vivo(porta_cdp):
                cofre._fechar_porta(porta_cdp)
            else:
                proc.terminate()
        except Exception:  # noqa: BLE001
            pass
    if not ok:
        log(f"{email}: não logou — nada gravado")
    return ok


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    main(int(sys.argv[1]))
