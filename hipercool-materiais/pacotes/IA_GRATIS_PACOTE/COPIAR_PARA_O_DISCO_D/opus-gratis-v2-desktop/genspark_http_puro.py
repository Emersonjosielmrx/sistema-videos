# -*- coding: utf-8 -*-
r"""genspark_http_puro.py — modo PURO: Genspark por HTTP puro, ZERO navegador (decisão da dona 31/10).

DESCOBERTA 31/10: o Genspark tinha fama de duas paredes (Cloudflare + g_recaptcha_token). Testado aqui:
  1. Cloudflare — o `requests` leva 403 "Just a moment" (TLS errado). **curl_cffi** impersonando o Chrome
     (mesmo JA3/TLS) + os cookies da sessão passam de boa (nem o cf_clearance precisou).
  2. `g_recaptcha_token` — o ask_proxy **NÃO o exige** para sessão já logada: POST com token VAZIO responde 200
     e devolve a resposta completa (medido: "391" em 4,5 s). Ou seja, dá pra fazer igual ao gemini_http:
     só cookies capturados 1x + curl_cffi. ZERO navegador, sem serviço pago.

Por isso o padrão é mandar SEM token. O **serviço de captcha** (CapSolver/2captcha) fica de BACKUP, caso um dia
o Genspark passe a exigir o token (a dona autorizou em 31/10; chave em `segredos/captcha.key`, formato
"capsolver:CAP-xxxx" ou "2captcha:xxxx"). GENSPARK_PURO_TOKEN = auto (padrão: vazio, cai pro serviço se preciso
e houver chave) | none (sempre vazio) | servico (sempre pelo serviço pago).

A site key/action vêm de `segredos/genspark_recaptcha.json` (descobertas pelo modo PÁGINA).

Uso:
    python genspark_http_puro.py capturar --conta conta_exemplo     # 1x: salva cookies da sessão
    python genspark_http_puro.py testar-cloudflare --conta conta_exemplo   # valida o Cloudflare (GET is_login)
    python genspark_http_puro.py --conta conta_exemplo "Quanto e 17 x 23?"  # pergunta (HTTP puro, sem navegador)
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # a própria pasta (portável: desktop, v2)
sys.path.insert(0, r"D:\logins-google")
import genspark as gs  # noqa: E402  (fila/cota/login/seletores)
import genspark_api as api  # noqa: E402

log = gs.log
BASE = Path(__file__).resolve().parent   # a própria pasta do projeto (portável: desktop, v2)
COOKIES_DIR = BASE / "cookies"
COOKIES_DIR.mkdir(exist_ok=True)
CAPTCHA_KEY_ARQ = BASE / "segredos" / "captcha.key"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/156.0.0.0 Safari/537.36")
PRAZO_S = int(os.environ.get("GENSPARK_PURO_PRAZO", "180"))
ACAO = os.environ.get("GENSPARK_RECAPTCHA_ACTION") or (api.ler_recaptcha_cfg().get("action") or "ai_chat")
TOKEN_MODO = os.environ.get("GENSPARK_PURO_TOKEN", "auto").lower()  # auto | none | servico


class SemCurlCffi(Exception):
    pass


class SemCookies(Exception):
    pass


class SemCaptcha(Exception):
    pass


def _curl():
    try:
        from curl_cffi import requests as creq  # noqa: PLC0415
        return creq
    except Exception as e:  # noqa: BLE001
        raise SemCurlCffi("curl_cffi não instalado. Rode: pip install curl_cffi") from e


# ─────────────────────── cookies (capturados 1x pelo cofre) ────────────────
def _arq_cookies(conta):
    return COOKIES_DIR / f"{conta}.json"


def capturar_cookies(conta):
    """Abre o Chrome do cofre uma vez, vai ao Genspark e salva os cookies (incl. cf_clearance) para o HTTP puro.
    É o equivalente ao sync_cookies.py do gemini-argo. NÃO é por mensagem — só quando o cf_clearance vencer."""
    from playwright.sync_api import sync_playwright
    import cofre  # noqa: PLC0415
    porta, proc = cofre.abrir(conta, url="about:blank")
    br = None
    try:
        with sync_playwright() as pw:
            br = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}", timeout=45000)
            ctx = br.contexts[0]
            pg = gs._pagina(ctx)
            gs._ir_chat(pg)
            # foca o campo p/ o Genspark carregar o reCAPTCHA (e confirmar que a sessão está viva)
            try:
                pg.locator("textarea").first.click(timeout=8000)
                time.sleep(3)
            except Exception:  # noqa: BLE001
                pass
            email = gs._sessao(pg)
            cookies = ctx.cookies("https://www.genspark.ai")
            dados = {"email": email, "ts": time.time(),
                     "cookies": {c["name"]: c["value"] for c in cookies}}
            _arq_cookies(conta).write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
            tem_cf = "cf_clearance" in dados["cookies"]
            print(f"{conta}: {len(dados['cookies'])} cookies salvos (cf_clearance={'sim' if tem_cf else 'NÃO'}; is_login={email!r})")
            return dados
    finally:
        cofre.fechar(proc, br, conta)


def capturar_todas():
    """Captura cookies de todas as contas logadas (1x, como o login). Uma por vez (1 Chrome por vez, RAM)."""
    dados = gs._ler()
    logadas = [c["apelido"] for c in dados["contas"] if c.get("logado")]
    print(f"Capturando cookies de {len(logadas)} conta(s) logada(s)...")
    for ap in logadas:
        try:
            capturar_cookies(ap)
        except Exception as e:  # noqa: BLE001
            print(f"  {ap}: ERRO {str(e)[:70]}")


def _carregar_cookies(conta):
    arq = _arq_cookies(conta)
    if not arq.exists():
        raise SemCookies(f"Sem cookies de {conta}. Rode: python genspark_http_puro.py capturar --conta {conta}")
    return json.loads(arq.read_text(encoding="utf-8")).get("cookies", {})


# ─────────────────────── token de captcha (serviço pago) ───────────────────
def _ler_captcha_key():
    if not CAPTCHA_KEY_ARQ.exists():
        raise SemCaptcha(f"Sem chave de captcha. Ponha '<provedor>:<KEY>' em {CAPTCHA_KEY_ARQ} "
                         f"(provedores: capsolver, 2captcha).")
    bruto = CAPTCHA_KEY_ARQ.read_text(encoding="utf-8").strip()
    if ":" in bruto:
        prov, chave = bruto.split(":", 1)
    else:
        prov, chave = "<SEGREDO_REMOVIDO>", bruto
    return prov.strip().lower(), chave.strip()


def token_recaptcha(sitekey=None, action=None, page_url=None):
    """Pede ao serviço de captcha um g_recaptcha_token (reCAPTCHA Enterprise v3/score). Retorna o token.
    Isto é o ÚNICO ponto que 'resolve' o reCAPTCHA — autorizado pela dona em 31/10."""
    sitekey = sitekey or api.sitekey()
    action = action or ACAO
    page_url = page_url or "https://www.genspark.ai/agents?type=ai_chat"
    prov, chave = _ler_captcha_key()
    import requests as rq  # noqa: PLC0415  (chamadas ao serviço, não ao Genspark)
    if prov == "capsolver":
        r = rq.post("https://api.capsolver.com/createTask", timeout=30, json={
            "clientKey": chave,
            "task": {"type": "ReCaptchaV3EnterpriseTaskProxyLess", "websiteURL": page_url,
                     "websiteKey": sitekey, "pageAction": action}}).json()
        if r.get("errorId"):
            raise SemCaptcha(f"CapSolver createTask: {r.get('errorCode')} {r.get('errorDescription')}")
        tid = r["taskId"]
        fim = time.time() + 120
        while time.time() < fim:
            time.sleep(3)
            g = rq.post("https://api.capsolver.com/getTaskResult", timeout=30,
                        json={"clientKey": chave, "taskId": tid}).json()
            if g.get("errorId"):
                raise SemCaptcha(f"CapSolver getTaskResult: {g.get('errorCode')} {g.get('errorDescription')}")
            if g.get("status") == "ready":
                return g["solution"]["gRecaptchaResponse"]
        raise SemCaptcha("CapSolver: tempo esgotado esperando o token")
    if prov == "2captcha":
        inp = rq.post("https://2captcha.com/in.php", timeout=30, data={
            "key": chave, "method": "userrecaptcha", "version": "v3", "enterprise": 1,
            "googlekey": sitekey, "action": action, "pageurl": page_url, "json": 1}).json()
        if inp.get("status") != 1:
            raise SemCaptcha(f"2captcha in.php: {inp.get('request')}")
        rid = inp["request"]
        fim = time.time() + 120
        while time.time() < fim:
            time.sleep(5)
            res = rq.get("https://2captcha.com/res.php", timeout=30,
                         params={"key": chave, "action": "get", "id": rid, "json": 1}).json()
            if res.get("status") == 1:
                return res["request"]
            if res.get("request") != "CAPCHA_NOT_READY":
                raise SemCaptcha(f"2captcha res.php: {res.get('request')}")
        raise SemCaptcha("2captcha: tempo esgotado esperando o token")
    raise SemCaptcha(f"provedor de captcha desconhecido: {prov}")


# ─────────────────────── chamada ao ask_proxy (HTTP puro) ───────────────────
def _headers(extra=None):
    h = {
        "user-agent": UA,
        "content-type": "application/json",
        "origin": "https://www.genspark.ai",
        "referer": "https://www.genspark.ai/agents?type=ai_chat",
        "x-timezone": "America/Sao_Paulo",
        "x-ask-dedupe": "1",
        "sec-ch-ua": '"Not:A-Brand";v="8", "Chromium";v="156", "Google Chrome";v="156"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "accept": "text/event-stream",
    }
    if extra:
        h.update(extra)
    return h


def testar_cloudflare(conta):
    """Só valida a parede 1 (Cloudflare): GET /api/is_login por HTTP puro com curl_cffi + cookies. NÃO precisa
    de reCAPTCHA. 200 + cogen_email = o curl_cffi+cf_clearance venceram o Cloudflare; aí só falta o token."""
    creq = _curl()
    cookies = _carregar_cookies(conta)
    r = creq.get("https://www.genspark.ai/api/is_login", cookies=cookies, headers=_headers(),
                 impersonate="chrome", timeout=30)
    corpo = r.text[:300]
    print(f"{conta}: HTTP {r.status_code} · {'Cloudflare' if 'Just a moment' in corpo or r.status_code==403 else 'passou'}")
    print("corpo:", corpo)
    return r.status_code == 200 and "cogen_email" in corpo


def _tem_captcha_key():
    return CAPTCHA_KEY_ARQ.exists() and CAPTCHA_KEY_ARQ.read_text(encoding="utf-8").strip() != ""


def _salvar_cookies_renovados(conta, resp):
    """Persiste cookies que o Genspark renovou na resposta (mantém a sessão fresca, como o gemini_http)."""
    try:
        novos = {c.name: c.value for c in resp.cookies.jar}
    except Exception:  # noqa: BLE001
        novos = {}
    if not novos:
        return
    try:
        dados = json.loads(_arq_cookies(conta).read_text(encoding="utf-8"))
        if dados.get("cookies", {}) | novos != dados.get("cookies"):
            dados.setdefault("cookies", {}).update(novos)
            _arq_cookies(conta).write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass


def _pedir(conta, prompt, model, token, bruto_arq=None):
    """Um POST ask_proxy por HTTP puro com o token dado ('' = sem token). Devolve (texto, status, corpo)."""
    creq = _curl()
    cookies = _carregar_cookies(conta)
    body = api.corpo_pedido(prompt, model=model)
    body["g_recaptcha_token"] = token or ""
    r = creq.post(api.ASK_URL, data=json.dumps(body).encode("utf-8"), cookies=cookies,
                  headers=_headers(), impersonate="chrome", timeout=PRAZO_S)
    _salvar_cookies_renovados(conta, r)
    corpo = r.text
    if bruto_arq:
        try:
            open(bruto_arq, "w", encoding="utf-8").write(corpo)
        except Exception:  # noqa: BLE001
            pass
    texto, _ev = api.parse_sse(corpo)
    return texto, r.status_code, corpo


def _precisa_token(status, corpo):
    """Heurística: a falha parece ser por reCAPTCHA (aí vale tentar o serviço de backup)?"""
    baixo = (corpo or "").lower()
    return status in (401, 403) or "recaptcha" in baixo or "g_recaptcha" in baixo or "captcha" in baixo or "verification" in baixo


def _conferir_aviso(conta, corpo, onde):
    """Levanta SemCota se o que veio é aviso do Genspark (crédito acabou / sem Opus), não resposta do modelo."""
    tipo = api.classificar(corpo)
    if tipo == "sem_credito":  # 31/10: "Você usou todos os seus créditos" passava como resposta (141 chars)
        raise gs.SemCota(f"créditos do dia acabaram nesta conta ({onde})")
    if tipo == "sem_opus":  # conta sem Opus 5.5 no grátis: pular de vez
        if hasattr(gs, "marcar_opus"):
            try:
                gs.marcar_opus(conta, False)
            except Exception:  # noqa: BLE001
                pass
        raise gs.SemCota(f"sem Opus 5.5 no grátis nesta conta ({onde})")


def _uma_puro(conta, prompt, model=None, bruto_arq=None, token_modo=None):
    modo = (token_modo or TOKEN_MODO).lower()
    # 1) caminho normal: SEM token (o ask_proxy não exige para sessão logada — medido 31/10)
    if modo != "servico":
        texto, status, corpo = _pedir(conta, prompt, model, "", bruto_arq)
        if status == 200 and texto:
            _conferir_aviso(conta, corpo, "puro")
            return texto
        if gs._tem_paywall(corpo.lower()):
            raise gs.SemCota("paywall do Genspark (puro)")
        if not (_precisa_token(status, corpo) and modo == "auto" and _tem_captcha_key()):
            raise RuntimeError(f"ask_proxy HTTP {status}: {(corpo or '')[:200]}")
        log.warning("puro: sem token falhou (HTTP %s) — tento o serviço de captcha (backup)", status)
    # 2) BACKUP: com token do serviço de captcha (a dona autorizou; custa dinheiro)
    token = token_recaptcha(sitekey=api.sitekey(), action=ACAO)
    texto, status, corpo = _pedir(conta, prompt, model, token, bruto_arq)
    if status != 200:
        if gs._tem_paywall(corpo.lower()):
            raise gs.SemCota("paywall do Genspark (puro+captcha)")
        raise RuntimeError(f"ask_proxy HTTP {status} (com token): {(corpo or '')[:200]}")
    _conferir_aviso(conta, corpo, "puro+captcha")
    if not texto:
        raise RuntimeError("resposta vazia (com token)")
    return texto


_SEM_COOKIE_AVISADA = set()


def perguntar(prompt, conta=None, tentativas=6, model=None, bruto_arq=None, token_modo=None):
    """Como genspark.perguntar, mas 100% HTTP puro (sem navegador). Precisa de cookies capturados.
    token_modo: None = GENSPARK_PURO_TOKEN (auto: sem token); "servico" = sempre com token do serviço de captcha pago
    (a linha "captcha" do /model) — sem chave em segredos/captcha.key levanta SemCaptcha com o motivo."""
    erros, ignorar, erro_final = 0, set(), None
    while erros < tentativas:
        try:
            apelido = conta or gs.proxima_conta(ignorar)
        except RuntimeError as e:
            log.warning("sem conta pronta no Genspark (puro): %s", e)
            return None
        t0 = time.time()
        try:
            resp = _uma_puro(apelido, prompt, model=model, bruto_arq=bruto_arq, token_modo=token_modo)
            if resp and resp.strip():
                gs.marcar_uso(apelido, sucesso=True, segundos=time.time() - t0)
                log.info("OK(puro) %s %.1fs %d chars", apelido, time.time() - t0, len(resp))
                return resp
            gs.marcar_uso(apelido, sucesso=False, erro_msg="resposta vazia")
            erro_final = "resposta vazia"
            erros += 1
        except gs.SemCota as e:
            log.warning("%s: %s — próxima conta", apelido, e)
            gs.marcar_sem_cota(apelido)
            ignorar.add(apelido)
            erro_final = str(e)
            if conta:
                break
        except SemCookies as e:  # só ESTA conta não tem cookie capturado: passa para a próxima (não gasta tentativa)
            if apelido not in _SEM_COOKIE_AVISADA:  # avisa 1x por conta (antes repetia 4 linhas a cada pedido)
                _SEM_COOKIE_AVISADA.add(apelido)
                log.warning("%s: %s — próxima conta (aviso só 1x)", apelido, e)
            ignorar.add(apelido)
            erro_final = str(e)
            if conta:
                if token_modo == "servico":
                    raise
                return None
        except (SemCaptcha, SemCurlCffi) as e:
            log.error("puro indisponível: %s", e)
            if token_modo == "servico":
                raise  # linha "captcha" pedida de propósito: o motivo (ex.: falta a chave) tem que chegar ao cliente
            return None
        except Exception as e:  # noqa: BLE001
            log.error("%s(puro): %s", apelido, str(e)[:150])
            gs.marcar_uso(apelido, sucesso=False, erro_msg=str(e))
            ignorar.add(apelido)
            erro_final = str(e)
            erros += 1
            if conta:
                break
        finally:
            if not conta:
                gs.soltar(apelido)
    log.error("Todas as tentativas falharam (puro): %s", erro_final)
    return None


def main():
    import argparse
    p = argparse.ArgumentParser(description="Genspark por HTTP puro (zero navegador; precisa de chave de captcha)")
    p.add_argument("cmd_ou_pergunta", nargs="?")
    p.add_argument("resto", nargs="*")
    p.add_argument("--conta")
    p.add_argument("--bruto", action="store_true")
    a = p.parse_args()
    cmd = a.cmd_ou_pergunta
    if cmd == "capturar":
        if a.conta:
            capturar_cookies(a.conta)
        else:
            capturar_todas()
    elif cmd == "testar-cloudflare":
        ok = testar_cloudflare(a.conta or "conta_exemplo")
        print("Cloudflare vencido:", ok)
    elif cmd:
        pergunta = " ".join([cmd, *a.resto])
        bruto = str(BASE / "captura" / "ask_proxy_puro_bruto.txt") if a.bruto else None
        t0 = time.time()
        r = perguntar(pergunta, conta=a.conta, bruto_arq=bruto)
        if r:
            print(r)
            print(f"\n[{time.time()-t0:.1f}s]", file=sys.stderr)
        else:
            print("ERRO: sem resposta", file=sys.stderr)
            sys.exit(1)
    else:
        p.print_help()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
