"""
SightEngine (censura/nudez): cria conta grátis em cada conta Google do cofre. SEMIAUTOMÁTICO.

Não tem login com Google: cadastro com o Gmail da conta + senha gerada (guardada antes de enviar) + termos.
O reCAPTCHA "Não sou um robô" quem clica é a pessoa (o robô espera até 8 min por conta); resolvido o captcha, o robô
clica em CREATE ACCOUNT.
Depois o robô abre o Gmail da conta no mesmo Chrome do cofre, abre o link de confirmação e copia
api_user/api_secret de /api-credentials. Valida com 1 análise (gasta 1 das 2.000 operações do mês).
Destino: D:\\postador-de-videos\\secrets\\sightengine.json ("keys"), lido pelo censura_visual.py.

CLI:
  python sightengine_contas.py criar <conta>
  python sightengine_contas.py criar_massa <conta1> <conta2> ...
  python sightengine_contas.py criar_massa --vivas
  python sightengine_contas.py listar
"""
import json
import re
import secrets
import struct
import sys
import time
import zlib
from datetime import date, datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, r"D:\logins-google")
import cofre

DIR = Path(__file__).resolve().parent
REGISTRO = DIR / "sightengine_contas.json"
DESTINO = Path(r"D:\postador-de-videos\secrets\sightengine.json")
SIGNUP = "https://dashboard.sightengine.com/signup"
CRED = "https://dashboard.sightengine.com/api-credentials"
GMAIL = "https://mail.google.com/mail/u/0/#search/from%3Asightengine"
ESPERA_CLIQUE = 480
LIMITE_REDE = "limite_de_contas_da_rede (SightEngine: 'Too many accounts have been created from your network')"


def _ler(arq, padrao):
    return json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else padrao


def _gravar(arq, dados):
    tmp = arq.with_suffix(".tmp")
    tmp.write_text(json.dumps(dados, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(arq)


def _registrar(conta, **campos):
    reg = _ler(REGISTRO, {})
    reg[conta] = {**reg.get(conta, {}), **campos}
    _gravar(REGISTRO, reg)
    return reg[conta]


def _png_cinza():
    w = h = 64
    bruto = b"".join(b"\x00" + b"\x80\x80\x80" * w for _ in range(h))

    def pedaco(tipo, dados):
        return struct.pack(">I", len(dados)) + tipo + dados + struct.pack(">I", zlib.crc32(tipo + dados) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + pedaco(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + pedaco(b"IDAT", zlib.compress(bruto)) + pedaco(b"IEND", b""))


def conferir(api_user, api_secret):
    """True = analisou uma imagem; False = recusou (resposta da API em erro); None = não conectou."""
    try:
        r = requests.post("https://api.sightengine.com/1.0/check.json", files={"media": ("t.png", _png_cinza())},
                          data={"models": "nudity-2.0", "api_user": api_user, "api_secret": api_secret}, timeout=40)
        return r.json().get("status") == "success"
    except (requests.RequestException, ValueError):
        return None


def _exportar(conta, api_user, api_secret):
    d = _ler(DESTINO, {"provider": "sightengine", "keys": []})
    if any(k.get("api_user") == api_user for k in d["keys"]):
        return
    d["keys"].append({"name": conta, "api_user": api_user, "api_secret": api_secret, "status": "available",
                      "used_today": 0, "used_at": date.today().isoformat()})
    _gravar(DESTINO, d)


def _print(page, motivo):
    p = DIR / f"_debug_se_{datetime.now():%H%M%S}_{motivo}.png"
    try:
        page.screenshot(path=str(p), timeout=15000)
    except Exception:
        pass
    return str(p)


def _ler_chaves(page):
    page.goto(CRED, timeout=60000)
    page.wait_for_timeout(6000)
    if "/api-credentials" not in page.url:
        return None, None
    m = re.search(r"API user\D*?(\d{6,12})", page.inner_text("body"))
    seg = page.locator("span.ak-secret[data-secret]")
    return (m.group(1) if m else None), (seg.first.get_attribute("data-secret") if seg.count() else None)


def _confirmar_email(ctx):
    """Abre o e-mail mais novo do SightEngine no Gmail da conta e segue o link de confirmação."""
    g = ctx.new_page()
    try:
        link = None
        fim = time.time() + 240
        while time.time() < fim and not link:
            g.goto(GMAIL, timeout=60000)
            g.wait_for_timeout(10000)
            linhas = g.locator("tr.zA")
            if not linhas.count():
                g.wait_for_timeout(15000)
                continue
            linhas.first.click()
            g.wait_for_timeout(6000)
            for a in g.locator("div.a3s a").all():
                h = a.get_attribute("href") or ""
                if "confirm-email-validation" in h:
                    link = h
                    break
        if link:
            g.goto(link, timeout=60000)
            g.wait_for_timeout(6000)
        return bool(link)
    finally:
        g.close()


def _esperar_clique(ctx, page):
    """Espera a pessoa resolver o captcha; com o captcha resolvido, o robô clica em CREATE ACCOUNT.
    True = alguma aba saiu do /signup para o painel; False = 8 min sem clique; None = limite de contas da rede."""
    fim, enviado = time.time() + ESPERA_CLIQUE, ""
    while time.time() < fim:
        page.wait_for_timeout(2000)
        for pg in ctx.pages:
            u = pg.url
            if "dashboard.sightengine.com" in u and not any(x in u for x in ("/signup", "/login")):
                return True
        try:
            corpo = page.inner_text("body")
            if "Too many accounts" in corpo:
                return None
            if "already exists with this email" in corpo:
                return "existe"
        except Exception:
            pass
        try:
            token = page.locator('textarea[name="g-recaptcha-response"]').first.input_value()
            if token and token != enviado and "/signup" in page.url:
                page.get_by_role("button", name="CREATE ACCOUNT").click(timeout=10000)
                enviado = token
        except Exception:
            pass
    return False



def criar_conta(conta, visivel=True):
    from playwright.sync_api import sync_playwright

    if _ler(REGISTRO, {}).get(conta, {}).get("valido"):
        return {"sucesso": True, "conta": conta, "nota": "já tinha"}
    if _ler(REGISTRO, {}).get(conta, {}).get("conta_ja_existe"):
        return {"sucesso": False, "conta": conta, "nota": "pulada: conta já existe no SightEngine (não criar)"}
    email, entrada = cofre.conta(conta)
    if entrada.get("google") != "vivo":
        return {"sucesso": False, "conta": conta, "erro": "google_deslogado_no_cofre (cofre.py logar)"}

    porta, proc = cofre.abrir(conta, url="about:blank", visivel=visivel)
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        ctx = br.contexts[0]
        page = ctx.new_page()
        try:
            api_user, api_secret = _ler_chaves(page)  # conta já criada e logada neste Chrome?
            if not api_secret:
                if "confirm-email" not in page.url:
                    senha = _ler(REGISTRO, {}).get(conta, {}).get("senha") or ("Se" + secrets.token_urlsafe(12) + "7a")
                    _registrar(conta, email=email, senha=senha)
                    page.goto(SIGNUP, timeout=60000)
                    page.wait_for_timeout(5000)
                    page.locator('input[name="email"]').fill(email)
                    page.locator('input[name="password"]').fill(senha)
                    page.locator('input[name="tos"]').check()
                    page.bring_to_front()
                    print(f"\n  >>> {conta}: clique em 'Não sou um robô' na janela do Chrome", flush=True)
                    passou = _esperar_clique(ctx, page)
                    if passou == "existe":  # dona 24/10: conta que já existe não se cria nem se insiste
                        _registrar(conta, conta_ja_existe=True)
                        return {"sucesso": False, "conta": conta, "nota": "pulada: conta já existe no SightEngine"}
                    if passou is None:
                        return {"sucesso": False, "conta": conta, "erro": LIMITE_REDE}
                    if not passou:
                        return {"sucesso": False, "conta": conta, "erro": "sem_clique_no_captcha (8 min)",
                                "print": _print(page, "captcha")}
                if not _confirmar_email(ctx):
                    return {"sucesso": False, "conta": conta, "erro": "email_de_confirmacao_nao_chegou"}
                api_user, api_secret = _ler_chaves(page)
            if not (api_user and api_secret):
                return {"sucesso": False, "conta": conta, "erro": "chaves_nao_encontradas", "print": _print(page, "chaves")}

            ok = conferir(api_user, api_secret)
            _registrar(conta, email=email, api_user=api_user, api_secret=api_secret, valido=ok,
                       criado_em=datetime.now(timezone.utc).isoformat(timespec="seconds"))
            if ok:
                _exportar(conta, api_user, api_secret)
            return {"sucesso": ok is True, "conta": conta, "api_user": api_user, "valido": ok}
        except Exception as e:
            return {"sucesso": False, "conta": conta, "erro": str(e)[:300], "print": _print(page, "erro")}
        finally:
            try:
                page.close()
            except Exception:
                pass
            cofre.fechar(proc, br, nome=conta)


def contas_vivas():
    return [v.get("apelido") or k.split("@")[0] for k, v in cofre._ler()["contas"].items() if v.get("google") == "vivo"]


def criar_massa(contas):
    resultados = []
    for c in contas:
        print(f"  {c}...", end=" ", flush=True)
        r = criar_conta(c)
        print(r.get("nota") or ("OK" if r.get("sucesso") else r.get("erro") or f"valido={r.get('valido')}"), flush=True)
        resultados.append(r)
        if r.get("erro") == LIMITE_REDE:
            print("  SightEngine não aceita mais contas desta rede: parei a fila.", flush=True)
            break
        if [str(x.get("erro")).startswith("sem_clique") for x in resultados[-2:]] == [True, True]:
            print("  2 contas seguidas sem clique no captcha: parei a fila (ninguém no PC?).", flush=True)
            break
    return resultados


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__)
    elif a[0] == "criar":
        print(json.dumps(criar_conta(a[1]), indent=2, ensure_ascii=False))
    elif a[0] == "criar_massa":
        res = criar_massa(contas_vivas() if "--vivas" in a else a[1:])
        print(f"\n{sum(1 for r in res if r.get('sucesso'))}/{len(res)} com chave no sightengine.json")
    elif a[0] == "listar":
        for c, v in _ler(REGISTRO, {}).items():
            print(f"{c:30s} api_user={v.get('api_user')}  valido={v.get('valido')}")
