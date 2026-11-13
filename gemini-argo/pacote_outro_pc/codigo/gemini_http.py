#!/usr/bin/env python3
r"""gemini_http.py — Cliente HTTP puro do Gemini (sem navegador).

Fala direto com o endpoint interno StreamGenerate do Gemini usando os cookies de
uma conta logada no cofre. Muito mais rápido e leve que abrir o Chrome: uma
chamada HTTP de ~2 s no lugar de 30-60 s de automação de navegador.

Os cookies são pegos UMA vez pelo navegador (sync_cookies.py) e cacheados em
cookies/<conta>.json; depois a própria sessão HTTP se mantém fresca pelo
Set-Cookie que o Gemini devolve a cada chamada.

Uso como módulo:
    from gemini_http import perguntar
    resposta = perguntar("Explique X", conta="emersonjosiel2030")

Uso CLI:
    python gemini_http.py "Explique X"
    python gemini_http.py --conta emersonjosiel2030 --modelo argon "Explique X"
"""
import json
import logging
import os
import re
import sys
import threading
import time
from pathlib import Path

import requests

sys.path.insert(0, r"D:\gemini-argo")
# Reaproveita a rotação/bloqueio de contas do cliente de navegador
from gemini_argon import proxima_conta, soltar, marcar_uso, marcar_sem_cota, adicionar_conta, _ler_contas

BASE = Path(r"D:\gemini-argo")
COOKIES_DIR = BASE / "cookies"
COOKIES_DIR.mkdir(exist_ok=True)

LOG_FILE = BASE / "argon_http.log"
logging.basicConfig(filename=str(LOG_FILE), level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger("argon_http")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36")

MODELOS = {
    "argon": "95a4c0abcba24364",
    "pro": "e6fa609c3fa255c0",
    "flash": "56fdd199312815e2",
    "flash-lite": "8c46e95b1a07cecc",
}

TIMEOUT = 300
TOKENS_VALIDADE = 1200  # revalida at/bl/f.sid a cada 20 min


class SemCookies(Exception):
    """Conta sem cookies cacheados — rode sync_cookies.py."""


class SemCota(Exception):
    """Pedimos o Argon e o Gemini serviu outro modelo (cota da conta acabou: 'Limite atingido. Continuando com o
    Flash-Lite.', ou conta sem o plano Pro). Visto 27/10: as 5 contas do rodízio respondiam Flash-Lite em silêncio."""


# Nome do modelo que o Gemini serviu de fato: ...,"<hash 16 hex>",null,null,"4 Argon",true,... (aspas escapadas no bruto)
_RE_SERVIDO = re.compile(r'\\?"[0-9a-f]{16}\\?",null,null,\\?"([^"\\]{2,40})\\?",(?:true|false)')


# 27/10: a resposta traz a hora EXATA em que a cota volta (a mesma que o navegador mostra: "redefinido, em 27 de
# out. (22:15)"), numa lista [recurso, [segundos, nanos], 1, null, [1]] por recurso
_RE_VOLTA = re.compile(r"\[\d+,\[(1\d{9}),\d+\],1,null,\[1\]\]")


def _buscar_volta(apelido):
    """Em segundo plano: o corte no 1º pedaço não traz a hora da volta (ela só vem no último pedaço, depois da resposta
    inteira). Pergunta curta na conta esgotada (quem responde é o Flash-Lite: não gasta Argon), lê a hora exata e
    corrige a fila. Fora do caminho do pedido do usuário."""
    def rodar():
        try:
            s = _carregar_sessao(apelido)
            at, bl, fsid = _tokens(apelido, s)
            freq, jspb = _pedido("Diga só: oi", "argon", "pt")
            url = ("https://gemini.google.com/_/BardChatUi/data/assistant.lamda.BardFrontendService/StreamGenerate"
                   f"?bl={bl}&f.sid={fsid}&hl=pt&_reqid={int(time.time()) % 1000000}&rt=c")
            r = s.post(url, data={"f.req": freq, "at": at}, timeout=120, headers={
                "Content-Type": "application/x-www-form-urlencoded;charset=utf-8", "x-same-domain": "1",
                "x-goog-ext-525001261-jspb": jspb, "Origin": "https://gemini.google.com",
                "Referer": "https://gemini.google.com/"})
            voltas = [int(v) for v in _RE_VOLTA.findall(r.text) if int(v) > time.time()]
            if voltas:
                marcar_sem_cota(apelido, volta=max(voltas))
        except Exception as e:  # noqa: BLE001 — fica a espera estimada
            log.warning("%s: não li a hora da volta (%s)", apelido, str(e)[:80])
    threading.Thread(target=rodar, daemon=True, name=f"volta-{apelido}").start()


def _conferir_servido(bruto, modelo):
    """Levanta SemCota (com .volta = epoch em que a cota volta, quando o Gemini informa) se pedimos o Argon e o
    trecho bruto da resposta mostra outro modelo."""
    if modelo != "argon":
        return
    servido = _RE_SERVIDO.findall(bruto)
    if servido and not any("argon" in s.lower() for s in servido):
        voltas = [int(v) for v in _RE_VOLTA.findall(bruto) if int(v) > time.time()]
        e = SemCota(f"servido {servido[-1]}" + (" (limite atingido)" if "Limite atingido" in bruto else " (sem Pro?)")
                    + (f", volta {time.strftime('%d/%m %H:%M', time.localtime(max(voltas)))}" if voltas else ""))
        e.volta = max(voltas) if voltas else None
        raise e


class AuthFalhou(Exception):
    """Cookies expiraram — a página não trouxe o token SNlM0e."""


# ─────────────────────── cookies ───────────────────────────────────────────
def _arq_cookies(conta):
    return COOKIES_DIR / f"{conta}.json"


def _carregar_sessao(conta):
    arq = _arq_cookies(conta)
    if not arq.exists():
        raise SemCookies(f"Sem cookies de {conta}. Rode: python sync_cookies.py {conta}")
    cookies = json.loads(arq.read_text(encoding="utf-8"))
    s = requests.Session()
    s.cookies.update(cookies)
    s.headers.update({"User-Agent": UA})
    return s


def _salvar_sessao(conta, sessao):
    """Persiste os cookies atuais (o Gemini renova 1PSIDCC/SIDCC a cada chamada)."""
    try:
        atuais = json.loads(_arq_cookies(conta).read_text(encoding="utf-8"))
    except Exception:
        atuais = {}
    atuais.update(sessao.cookies.get_dict())
    tmp = _arq_cookies(conta).with_suffix(".tmp")
    tmp.write_text(json.dumps(atuais, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(_arq_cookies(conta))


# ─────────────────────── tokens da página ──────────────────────────────────
_cache_tokens = {}  # conta -> (ts, at, bl, fsid)


def _tokens(conta, sessao):
    agora = time.time()
    c = _cache_tokens.get(conta)
    if c and agora - c[0] < TOKENS_VALIDADE:
        return c[1], c[2], c[3]
    r = sessao.get("https://gemini.google.com/app", timeout=30)
    html = r.text

    def pega(chave):
        m = re.search(r'"%s":"([^"]+)"' % chave, html)
        return m.group(1) if m else None

    at, bl, fsid = pega("SNlM0e"), pega("cfb2h"), pega("FdrFJe")
    if not at:
        raise AuthFalhou(f"Cookies de {conta} expiraram (sem SNlM0e). Rode sync_cookies.py {conta}")
    _cache_tokens[conta] = (agora, at, bl, fsid)
    return at, bl, fsid


_lock_resync = threading.Lock()


def _abrir(conta):
    """Sessão pronta para uso. Se os cookies venceram (o Chrome do cofre gira o 1PSIDTS sempre que abre a conta,
    e a nossa cópia morre em horas), pega cookies novos pelo cofre e tenta de novo, sem intervenção."""
    try:
        s = _carregar_sessao(conta)
        _tokens(conta, s)
        return s
    except (SemCookies, AuthFalhou) as e:
        log.warning("%s: %s — ressincronizando pelo cofre", conta, e)
    with _lock_resync:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import sync_cookies
        if not sync_cookies.sincronizar(conta):
            raise AuthFalhou(f"{conta}: ressincronização pelo cofre falhou (conta deslogada?)")
    _cache_tokens.pop(conta, None)
    s = _carregar_sessao(conta)
    _tokens(conta, s)
    return s


# ─────────────────────── parse da resposta ─────────────────────────────────
def _parse(body):
    """Extrai o texto final da resposta streaming do StreamGenerate.

    O corpo tem vários frames [["wrb.fr",...]] cumulativos; o texto completo
    está no último frame que traz um candidato. Retorna (texto, cid, rid, rcid).
    """
    melhor_texto, cid, rid, rcid = None, None, None, None
    for linha in body.split("\n"):
        linha = linha.strip()
        if not linha.startswith("[["):
            continue
        try:
            arr = json.loads(linha)
        except Exception:
            continue
        for item in arr:
            if not (isinstance(item, list) and item and item[0] == "wrb.fr" and len(item) > 2 and item[2]):
                continue
            try:
                data = json.loads(item[2])
            except Exception:
                continue
            if not isinstance(data, list) or len(data) <= 4:
                continue
            # IDs de conversa: data[1] = [cid, rid]
            if len(data) > 1 and isinstance(data[1], list) and len(data[1]) >= 2:
                cid, rid = data[1][0], data[1][1]
            if data[4]:
                cand = data[4][0]
                if isinstance(cand, list) and len(cand) > 1:
                    if cand[0]:
                        rcid = cand[0]
                    if cand[1] and isinstance(cand[1], list) and cand[1][0]:
                        t = cand[1][0]
                        # fica com o maior (os frames são cumulativos)
                        if melhor_texto is None or len(t) >= len(melhor_texto):
                            melhor_texto = t
    return melhor_texto, cid, rid, rcid


# ─────────────────────── chamada principal ─────────────────────────────────
# 27/10: nível de raciocínio. Sem ele o Gemini usa o padrão da conta (mais raso). Achado comparando o navegador com
# Baixo/Médio/Alto: no corpo f.req[68] e no cabeçalho jspb[11] (no app novo, processSession campo 18: Baixo 3,
# Médio 0, Alto 2). Medido: com 2 o Argon leva ~2,4x mais (10 s -> 25 s) e chega a rodar código para conferir.
NIVEL_RACIOCINIO = int(os.environ.get("ARGON_NIVEL", "2"))


def _pedido(prompt, modelo, idioma):
    """(f.req, cabeçalho jspb) do StreamGenerate; o Argon sempre com o nível de raciocínio Alto."""
    inner = [[prompt, 0, None, None, None, None, 0], [idioma], None]
    jspb = [1, None, None, None, MODELOS.get(modelo, MODELOS["argon"])]
    if modelo == "argon":
        inner += [None] * (69 - len(inner))
        inner[68] = NIVEL_RACIOCINIO
        jspb += [None] * (12 - len(jspb))
        jspb[11] = NIVEL_RACIOCINIO
    return json.dumps([None, json.dumps(inner, ensure_ascii=False)], ensure_ascii=False), json.dumps(jspb)


def _uma_chamada(sessao, conta, prompt, modelo, idioma="pt"):
    at, bl, fsid = _tokens(conta, sessao)
    freq, jspb = _pedido(prompt, modelo, idioma)

    url = ("https://gemini.google.com/_/BardChatUi/data/"
           "assistant.lamda.BardFrontendService/StreamGenerate"
           f"?bl={bl}&f.sid={fsid}&hl={idioma}&_reqid={int(time.time()) % 1000000}&rt=c")
    headers = {
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
        "x-same-domain": "1",
        "x-goog-ext-525001261-jspb": jspb,
        "Origin": "https://gemini.google.com",
        "Referer": "https://gemini.google.com/",
    }
    # 27/10: lido aos poucos para cortar no 1º pedaço se o Gemini não serviu o Argon (antes o Flash-Lite respondia
    # inteiro, 10-30 s jogados fora, para só então trocar de conta)
    r = sessao.post(url, data={"f.req": freq, "at": at}, headers=headers, timeout=TIMEOUT, stream=True)
    if r.status_code != 200:
        raise RuntimeError(f"StreamGenerate HTTP {r.status_code}: {r.text[:300]}")
    partes, conferido = [], False
    try:
        for linha in r.iter_lines(decode_unicode=True):
            if not linha:
                continue
            partes.append(linha)
            if not conferido and _RE_SERVIDO.search(linha):
                _conferir_servido(linha, modelo)
                conferido = True
    finally:
        r.close()
    bruto = "\n".join(partes)
    if not conferido:
        _conferir_servido(bruto, modelo)
    texto, cid, rid, rcid = _parse(bruto)
    return texto


def _stream_chamada(sessao, conta, prompt, modelo, idioma="pt"):
    """Igual a _uma_chamada, mas cede (yield) os deltas de texto conforme chegam."""
    at, bl, fsid = _tokens(conta, sessao)
    freq, jspb = _pedido(prompt, modelo, idioma)
    url = ("https://gemini.google.com/_/BardChatUi/data/"
           "assistant.lamda.BardFrontendService/StreamGenerate"
           f"?bl={bl}&f.sid={fsid}&hl={idioma}&_reqid={int(time.time()) % 1000000}&rt=c")
    headers = {
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
        "x-same-domain": "1",
        "x-goog-ext-525001261-jspb": jspb,
        "Origin": "https://gemini.google.com",
        "Referer": "https://gemini.google.com/",
    }
    r = sessao.post(url, data={"f.req": freq, "at": at}, headers=headers, timeout=TIMEOUT, stream=True)
    if r.status_code != 200:
        raise RuntimeError(f"StreamGenerate HTTP {r.status_code}")
    enviado = ""
    for linha in r.iter_lines(decode_unicode=True):
        if not linha or not linha.strip().startswith("[["):
            continue
        if not enviado:  # antes do 1º pedaço: se não é o Argon, a próxima conta responde no lugar
            _conferir_servido(linha, modelo)
        try:
            arr = json.loads(linha.strip())
        except Exception:
            continue
        for item in arr:
            if not (isinstance(item, list) and item and item[0] == "wrb.fr" and len(item) > 2 and item[2]):
                continue
            try:
                data = json.loads(item[2])
            except Exception:
                continue
            if isinstance(data, list) and len(data) > 4 and data[4]:
                cand = data[4][0]
                if isinstance(cand, list) and len(cand) > 1 and cand[1] and cand[1][0]:
                    completo = cand[1][0]
                    if len(completo) > len(enviado) and completo.startswith(enviado):
                        yield completo[len(enviado):]
                        enviado = completo
                    elif completo != enviado and len(completo) >= len(enviado):
                        # frame reescreveu o texto: manda o completo
                        yield completo
                        enviado = completo
    if not enviado:
        raise RuntimeError("resposta vazia")


def perguntar_stream(prompt, conta=None, modelo="argon", idioma="pt", tentativas=6):
    """Versão geradora: cede deltas de texto. Usa conta fixa ou a primeira pronta da fila.
    Conta sem cota do Argon (SemCota, detectada antes do 1º pedaço) sai da fila com hora de volta e a próxima
    responde; isso não gasta tentativa. Fila vazia = erro na hora (proxima_conta)."""
    erros = 0
    while erros < tentativas:
        apelido = conta or proxima_conta()
        mandou = False
        try:
            sessao = _abrir(apelido)
            for delta in _stream_chamada(sessao, apelido, prompt, modelo, idioma):
                mandou = True
                yield delta
            _salvar_sessao(apelido, sessao)
            marcar_uso(apelido, sucesso=True)
            return
        except SemCota as e:
            log.warning("%s: %s — próxima conta", apelido, e)
            marcar_sem_cota(apelido, volta=getattr(e, "volta", None))
            if not getattr(e, "volta", None):
                _buscar_volta(apelido)
            if conta or mandou:
                raise
        except Exception as e:
            marcar_uso(apelido, sucesso=False, erro_msg=str(e))
            raise
        finally:
            if not conta:
                soltar(apelido)
    raise RuntimeError(f"{tentativas} erros seguidos no Argon")


def perguntar(prompt, conta=None, modelo="argon", idioma="pt", tentativas=6):
    """Pergunta ao Gemini (Argon por padrão) via HTTP puro. Retorna o texto ou None.

    Fila de contas: usa a primeira pronta; sem cota (cortada no 1º pedaço) sai com hora de volta e a próxima responde
    sem gastar tentativa; outros erros gastam tentativa. Fila vazia = RuntimeError na hora (proxima_conta).
    """
    erro_final = None
    erros = 0
    while erros < tentativas:
        apelido = conta or proxima_conta()
        t0 = time.time()
        try:
            sessao = _abrir(apelido)
            texto = _uma_chamada(sessao, apelido, prompt, modelo, idioma)
            _salvar_sessao(apelido, sessao)
            if texto and texto.strip():
                marcar_uso(apelido, sucesso=True)
                log.info("OK %s modelo=%s %.1fs %d chars", apelido, modelo, time.time() - t0, len(texto))
                return texto
            marcar_uso(apelido, sucesso=False, erro_msg="resposta vazia")
            erro_final = "resposta vazia"
            erros += 1
        except SemCota as e:
            log.warning("%s: %s — próxima conta (%.1fs)", apelido, e, time.time() - t0)
            marcar_sem_cota(apelido, volta=getattr(e, "volta", None))
            if not getattr(e, "volta", None):
                _buscar_volta(apelido)
            erro_final = str(e)
        except (SemCookies, AuthFalhou) as e:
            log.warning("%s: %s", apelido, e)
            marcar_uso(apelido, sucesso=False, erro_msg=str(e))
            erro_final = str(e)
            erros += 1
        except Exception as e:
            log.error("%s: %s", apelido, e)
            marcar_uso(apelido, sucesso=False, erro_msg=str(e))
            erro_final = str(e)
            erros += 1
        finally:
            if not conta:
                soltar(apelido)
        if conta:  # conta fixa: não rodar outras
            break
    log.error("Todas as tentativas falharam: %s", erro_final)
    return None


def main():
    import argparse
    p = argparse.ArgumentParser(description="Perguntar ao Gemini via HTTP puro (sem navegador)")
    p.add_argument("pergunta", nargs="?")
    p.add_argument("--conta")
    p.add_argument("--modelo", default="argon", choices=list(MODELOS))
    p.add_argument("--listar", action="store_true")
    args = p.parse_args()

    if args.listar:
        dados = _ler_contas()
        for c in dados["contas"]:
            tem = _arq_cookies(c["apelido"]).exists()
            print(f"  {c['apelido']:35} cookies={'sim' if tem else 'NAO':3} "
                  f"{'BLOQUEADA' if c.get('bloqueada') else 'ok'}")
        return

    if not args.pergunta:
        p.print_help()
        return

    t0 = time.time()
    r = perguntar(args.pergunta, conta=args.conta, modelo=args.modelo)
    if r:
        print(r)
        print(f"\n[{time.time()-t0:.1f}s]", file=sys.stderr)
    else:
        print("ERRO: sem resposta", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
