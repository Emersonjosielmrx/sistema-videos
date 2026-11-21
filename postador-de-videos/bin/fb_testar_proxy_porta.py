"""Testa se a sessão logada numa janela (porta CDP) continua válida saindo por um proxy Webshare (rnprmtfo-N).
Pega os cookies da janela e fala com o FB por HTTP, direto (casa) e pelo proxy. Não digita nada.
    python fb_testar_proxy_porta.py <porta> <N>"""
import re, sys
sys.path.insert(0, r"D:\logins-google"); sys.path.insert(0, r"D:\hipercool-materiais\comum\fish_audio")
import fish_audio
from playwright.sync_api import sync_playwright
from curl_cffi import requests as creq

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
porta, N = int(sys.argv[1]), int(sys.argv[2])
with sync_playwright() as p:
    ctx = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}").contexts[0]
    cookies = ctx.cookies("https://www.facebook.com")
ck = {c["name"]: c["value"] for c in cookies}
print("c_user:", ck.get("c_user"), flush=True)
if "c_user" not in ck:
    sys.exit("janela não logada")


def testar(nome, proxy):
    s = creq.Session(impersonate="chrome", proxies={"http": proxy, "https": proxy} if proxy else None)
    for c in cookies:
        s.cookies.set(c["name"], c["value"], domain=c["domain"], path=c["path"])
    try:
        ip = s.get("http://ip-api.com/json/?fields=query,isp", timeout=30).json()
    except Exception:
        ip = {}
    r = s.get("https://www.facebook.com/me", timeout=40, allow_redirects=True)
    t = r.text
    logada = f'"USER_ID":"{ck["c_user"]}"' in t or f'"ACCOUNT_ID":"{ck["c_user"]}"' in t
    caiu = "/login" in str(r.url) or "login_form" in t
    nome_p = (re.search(r'"NAME":"([^"]+)"', t) or ["", "?"])[1]
    print(f"  [{nome}] IP {ip.get('query')} ({ip.get('isp')}) -> "
          f"{'LOGADA ('+nome_p+')' if logada else 'CAIU PRO LOGIN' if caiu else 'incerto/bloqueio'}", flush=True)
    return logada


testar("casa", None)
px = f"http://127.0.0.1:{fish_audio._subir_ponte(N)}"
ok = testar(f"webshare-{N}", px)
print(f"VEREDITO: {'pode usar o Webshare -'+str(N) if ok else 'NÃO sobreviveu — manter casa'}", flush=True)
