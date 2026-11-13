# -*- coding: utf-8 -*-
"""auto_login.py - garante sessao HeyGen logada via CDP.

Fluxo:
  1. conecta no Chrome CDP (porta 9225)
  2. abre app.heygen.com/home
  3. se ja logado -> retorna True
  4. se caiu na tela de login -> preenche email+senha, clica "Log in"
  5. verifica que saiu da tela de login

Uso:
  python auto_login.py
  (chamar ANTES de run_one.py; se sessao expirou, faz login sozinho)

Credenciais: vem de env HEYGEN_EMAIL / HEYGEN_PASS,
ou do arquivo _CREDENCIAIS_HEYGEN.txt (linha1=email, linha2=senha).
"""
import asyncio, json, os, sys, time, urllib.request
from pathlib import Path
import websockets

CDP_PORT = int(os.environ.get("HEYGEN_CDP_PORT", "9225"))
CRED_FILE = Path("D:/roteador-heygen-api/_CREDENCIAIS_HEYGEN.txt")


def flush(m):
    print("[" + time.strftime("%H:%M:%S") + "] " + str(m), flush=True)


def load_creds():
    email = os.environ.get("HEYGEN_EMAIL", "")
    senha = os.environ.get("HEYGEN_PASS", "")
    if (not email or not senha) and CRED_FILE.exists():
        lines = [l.strip() for l in CRED_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
        if len(lines) >= 2:
            email, senha = lines[0], lines[1]
    return email, senha


async def _call(ws, state, method, params=None):
    state["id"] += 1
    mid = state["id"]
    await ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
    for _ in range(240):
        try:
            d = json.loads(await asyncio.wait_for(ws.recv(), timeout=0.5))
        except asyncio.TimeoutError:
            continue
        if d.get("id") == mid:
            return d
    return {"error": "timeout"}


async def _js(ws, state, expr):
    r = await _call(ws, state, "Runtime.evaluate", {"expression": expr, "returnByValue": True})
    res = r.get("result", {})
    if "exceptionDetails" in res:
        return None
    return res.get("result", {}).get("value")


def _is_logged(url):
    return url and "app.heygen.com" in url and "/login" not in url and "auth.heygen" not in url


async def ensure_login():
    email, senha = load_creds()
    if not email or not senha:
        flush("[ERRO] sem credenciais (defina HEYGEN_EMAIL/HEYGEN_PASS ou _CREDENCIAIS_HEYGEN.txt)")
        return False

    tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/list").read())
    tab = next((t for t in tabs if t.get("type") == "page"), tabs[0])
    async with websockets.connect(tab["webSocketDebuggerUrl"], max_size=50 * 1024 * 1024,
                                  ping_interval=None, open_timeout=10) as ws:
        state = {"id": 0}
        await _call(ws, state, "Page.enable")
        await _call(ws, state, "Runtime.enable")

        # navega pra home
        await _call(ws, state, "Page.navigate", {"url": "https://app.heygen.com/home"})
        await asyncio.sleep(4)
        # espera ate o conteudo realmente carregar (sessoes persistem via cookie,
        # mas o React precisa hidratar; se chegar antes, mostra landing)
        for _try in range(15):
            url = await _js(ws, state, "location.href") or ""
            body = await _js(ws, state, "(document.body.innerText||'').slice(0,400)") or ""
            logged_content = ("Sign in with Google" not in body and "Sign in with Apple" not in body
                              and "Two-Factor" not in body and "6-digit" not in body)
            if _is_logged(url) and logged_content:
                flush("[login] ja logado (" + url[:40] + ") hidrate ok")
                return True
            # se body tem sinais de login, precisa logar
            if "Sign in with Google" in body or "Sign in with Apple" in body:
                break
            # landing ainda hidratando: espera mais
            await asyncio.sleep(1)
        # Se chegou aqui, /home nao mostrou dashboard. Pode ser sessao valida
        # mas a pagina levou mais tempo. Vamos testar /create-v4/draft para confirmar
        # se a sessao esta persistindo em rotas autenticadas.
        await _call(ws, state, "Page.navigate", {"url": "https://app.heygen.com/create-v4/draft?vt=l"})
        await asyncio.sleep(6)
        url = await _js(ws, state, "location.href") or ""
        body = await _js(ws, state, "(document.body.innerText||'').slice(0,400)") or ""
        if "create-v4" in url and "Sign in with" not in body and "6-digit" not in body:
            flush("[login] sessao valida (" + url[:50] + ")")
            return True
        # ainda precisa logar - volta pra home
        await _call(ws, state, "Page.navigate", {"url": "https://app.heygen.com/home"})
        await asyncio.sleep(3)
        url = await _js(ws, state, "location.href") or ""
        if _is_logged(url):
            flush("[login] URL ok mas conteudo suspeito: " + body[:60].replace("\n"," "))
        else:
            flush("[login] URL=" + url[:40] + " - precisa logar")

        flush("[login] sessao caiu, fazendo login com " + email)
        SET = "var s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;"

        # preenche email
        await _js(ws, state, SET + "(function(){var i=null;document.querySelectorAll('input[type=email]')"
                  ".forEach(function(e){var r=e.getBoundingClientRect();if(r.width>0&&e.offsetParent!==null)i=e;});"
                  "if(!i)return;s.call(i," + json.dumps(email) + ");"
                  "i.dispatchEvent(new Event('input',{bubbles:true}));i.dispatchEvent(new Event('change',{bubbles:true}));})()")
        await asyncio.sleep(0.4)

        # clica "Use password"
        await _js(ws, state, "(function(){var b=document.querySelectorAll('button');for(var i=0;i<b.length;i++)"
                  "{if((b[i].textContent||'').trim()==='Use password'){b[i].click();return;}}})()")

        # espera campo password aparecer
        for _ in range(16):
            await asyncio.sleep(0.5)
            n = await _js(ws, state, "document.querySelectorAll('input[type=password]').length")
            if n and n > 0:
                break
        else:
            flush("[ERRO] campo de senha nao apareceu")
            return False

        # reforca email (o slide password tem seu proprio input) + senha
        await _js(ws, state, SET + "(function(){var i=null;document.querySelectorAll('input[type=email]')"
                  ".forEach(function(e){var r=e.getBoundingClientRect();if(r.width>0&&e.offsetParent!==null)i=e;});"
                  "if(i){s.call(i," + json.dumps(email) + ");i.dispatchEvent(new Event('input',{bubbles:true}));"
                  "i.dispatchEvent(new Event('change',{bubbles:true}));}})()")
        await _js(ws, state, SET + "(function(){var p=document.querySelector('input[type=password]');if(!p)return;"
                  "s.call(p," + json.dumps(senha) + ");p.dispatchEvent(new Event('input',{bubbles:true}));"
                  "p.dispatchEvent(new Event('change',{bubbles:true}));})()")
        await asyncio.sleep(0.6)

        # clica "Log in"
        await _js(ws, state, "(function(){var b=document.querySelectorAll('button');for(var i=0;i<b.length;i++)"
                  "{var r=b[i].getBoundingClientRect();if((b[i].textContent||'').trim()==='Log in'&&r.width>0)"
                  "{b[i].click();return;}}})()")

        # aguarda sair da tela de login
        for i in range(20):
            await asyncio.sleep(1)
            url = await _js(ws, state, "location.href") or ""
            if _is_logged(url):
                flush("[login] OK -> " + url[:40])
                return True
            txt = await _js(ws, state, "(document.body.innerText||'').slice(0,200)") or ""
            if any(k in txt.lower() for k in ["6-digit", "two-factor", "authenticator", "verification code"]):
                if i >= 6:  # deu tempo e ainda pede 2FA
                    flush("[ATENCAO] pediu 2FA - precisa de codigo manual")
                    return False
        flush("[ERRO] login nao completou (url=" + url[:40] + ")")
        return False


if __name__ == "__main__":
    ok = asyncio.run(ensure_login())
    sys.exit(0 if ok else 1)
