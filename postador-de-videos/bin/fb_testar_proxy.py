"""Testa se a sessão do Facebook (logada pela CASA) continua valendo quando o tráfego sai pelo Webshare da conta.
Dona 20/11: 1 perfil usa a casa; os outros têm que usar o Webshare grátis de cada um — então a conta logada pela casa
precisa continuar de pé no IP do Webshare dela.

Não loga, não digita, não abre Chrome: pega os cookies da janela JÁ logada (porta do cofre) e fala com o Facebook por
HTTP (curl_cffi, impersonate=chrome) DUAS vezes — uma direto (casa) e uma pelo proxy da conta — comparando se continua
logada e qual IP o Facebook vê.

    python fb_testar_proxy.py <email>
"""
import re, sys
from pathlib import Path

sys.path.insert(0, r"D:\logins-google"); sys.path.insert(0, r"D:\hipercool-materiais\comum\fish_audio")
import fish_audio
from playwright.sync_api import sync_playwright
from curl_cffi import requests as creq

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
email = sys.argv[1]
cofre, n = fish_audio.checar_conta(email)
_, e = cofre.conta(email)
porta = e["porta"]

with sync_playwright() as p:
    ctx = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}").contexts[0]
    cookies = ctx.cookies("https://www.facebook.com")
ck = {c["name"]: c["value"] for c in cookies}
print(f"== {email}: c_user na janela = {ck.get('c_user')}", flush=True)
if "c_user" not in ck:
    print("janela não está logada — nada a testar", flush=True)
    sys.exit(0)


def sessao(proxy):
    s = creq.Session(impersonate="chrome", proxies={"http": proxy, "https": proxy} if proxy else None)
    for c in cookies:
        s.cookies.set(c["name"], c["value"], domain=c["domain"], path=c["path"])
    return s


def testar(nome, proxy):
    try:
        s = sessao(proxy)
        ip = s.get("http://ip-api.com/json/?fields=query,isp,hosting", timeout=30).json()
    except Exception as x:
        print(f"  [{nome}] não mediu IP: {str(x)[:80]}", flush=True); ip = {}
    try:
        r = s.get("https://www.facebook.com/me", timeout=40, allow_redirects=True)
        t = r.text
        logada = ("USER_ID" in t and f'"USER_ID":"{ck["c_user"]}"' in t) or f'"ACCOUNT_ID":"{ck["c_user"]}"' in t
        caiu = "/login" in str(r.url) or "login_form" in t
        bloq = bool(re.search(r"checkpoint|Insira os caracteres|temporariamente", t[:50000], re.I))
        nome_perfil = (re.search(r'"NAME":"([^"]+)"', t) or ["", "?"])[1]
        print(f"  [{nome}] IP {ip.get('query')} ({ip.get('isp')}) -> "
              f"{'LOGADA ('+nome_perfil+')' if logada else 'CAIU PRO LOGIN' if caiu else 'BLOQUEIO/CAPTCHA' if bloq else 'incerto'}",
              flush=True)
        return logada
    except Exception as x:
        print(f"  [{nome}] erro: {str(x)[:120]}", flush=True)
        return None


print("teste 1: direto (casa)", flush=True)
testar("casa", None)
px = f"http://127.0.0.1:{fish_audio._subir_ponte(n)}"
print(f"teste 2: pelo Webshare da conta (rnprmtfo-{n})", flush=True)
ok = testar("webshare", px)
print(f"\nVEREDITO: a sessão {'CONTINUA válida' if ok else 'NÃO sobreviveu'} no IP do Webshare "
      f"-> {'pode usar o proxy nesta conta' if ok else 'manter na casa ou re-logar pelo proxy'}", flush=True)
