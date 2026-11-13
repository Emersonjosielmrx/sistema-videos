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
from gemini_argon import (proxima_conta, soltar, marcar_uso, marcar_sem_cota, adicionar_conta, _ler_contas,  # noqa: F401
                          marcar_cookies, pronta)

BASE = Path(r"D:\gemini-argo")
COOKIES_DIR = BASE / "cookies"
COOKIES_DIR.mkdir(exist_ok=True)

# 29/10 (Fable): tudo vai para o argon.log (o basicConfig do gemini_argon já ligou antes); aqui só troca o handler por
# um com rotação (5 MB × 5) — o arquivo tinha 135 KB/dia e nunca girava.
from logging.handlers import RotatingFileHandler  # noqa: E402
for _h in list(logging.root.handlers):
    if isinstance(_h, logging.FileHandler) and not isinstance(_h, RotatingFileHandler):
        logging.root.removeHandler(_h)
        _r = RotatingFileHandler(_h.baseFilename, maxBytes=5_000_000, backupCount=5, encoding="utf-8")
        _r.setFormatter(_h.formatter)
        logging.root.addHandler(_r)
log = logging.getLogger("argon_http")
PRAZO_TOTAL = int(os.environ.get("ARGON_PRAZO_S", "580"))  # abaixo dos 600 s do proxy da VPS (resposta depois disso é cota jogada fora)

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
            url, headers = _url_headers(bl, fsid, "pt", jspb)
            r = s.post(url, data={"f.req": freq, "at": at}, timeout=120, headers=headers)
            voltas = [int(v) for v in _RE_VOLTA.findall(r.text) if int(v) > time.time()]
            if voltas:
                marcar_sem_cota(apelido, volta=max(voltas))
        except Exception as e:  # noqa: BLE001 — fica a espera estimada
            log.warning("%s: não li a hora da volta (%s)", apelido, str(e)[:80])
    threading.Thread(target=rodar, daemon=True, name=f"volta-{apelido}").start()


_NOME_SERVIDO = {"argon": "argon", "pro": "pro"}  # 29/10: o Pro (servido "3.1 Pro") divide a cota com o Argon


def _conferir_servido(bruto, modelo):
    """Levanta SemCota (com .volta = epoch em que a cota volta, quando o Gemini informa) se pedimos o Argon ou o Pro e
    o trecho bruto da resposta mostra outro modelo (o Google troca pelo Flash-Lite calado quando a cota acaba)."""
    esperado = _NOME_SERVIDO.get(modelo)
    if not esperado:
        return
    servido = _RE_SERVIDO.findall(bruto)
    if servido and not any(esperado in s.lower() for s in servido):
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


_SESSOES = {}  # conta -> (mtime do cookies.json, Session)  29/10 (Fable): 1 Session por conta (reaproveita a conexão TLS)
_trava_sessoes = threading.Lock()


def _carregar_sessao(conta):
    arq = _arq_cookies(conta)
    if not arq.exists():
        raise SemCookies(f"Sem cookies de {conta}. Rode: python sync_cookies.py {conta}")
    mt = arq.stat().st_mtime
    with _trava_sessoes:
        c = _SESSOES.get(conta)
        if c and c[0] == mt:
            return c[1]
        cookies = json.loads(arq.read_text(encoding="utf-8"))
        s = requests.Session()
        s.cookies.update(cookies)
        s.headers.update({"User-Agent": UA})
        s._carregado = dict(cookies)  # para gravar só o que mudou nesta sessão
        _SESSOES[conta] = (mt, s)
        return s


def _salvar_sessao(conta, sessao):
    """Persiste os cookies que ESTA sessão renovou (o Gemini renova 1PSIDCC/SIDCC a cada chamada). 29/10 (Fable): só os
    que mudaram em relação ao que a sessão carregou — antes regravava todos e um pedido longo desfazia o cookie novo que o
    cofre acabara de gravar (conta voltava a "sem SNlM0e")."""
    base = getattr(sessao, "_carregado", {})
    novos = {k: v for k, v in sessao.cookies.get_dict().items() if base.get(k) != v}
    if not novos:
        return
    with _trava_sessoes:
        try:
            atuais = json.loads(_arq_cookies(conta).read_text(encoding="utf-8"))
        except Exception:
            atuais = {}
        atuais.update(novos)
        tmp = _arq_cookies(conta).with_suffix(f".{os.getpid()}.tmp")
        tmp.write_text(json.dumps(atuais, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(_arq_cookies(conta))
        sessao._carregado = dict(atuais)
        if conta in _SESSOES:
            _SESSOES[conta] = (_arq_cookies(conta).stat().st_mtime, sessao)


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


_lock_resync = threading.Lock()  # o cofre abre 1 Chrome por vez


class TrocarConta(Exception):
    """Cookies desta conta morreram e há outra pronta: o pedido segue na próxima, sem esperar o Chrome."""


def _outra_pronta(conta):
    from datetime import datetime
    iso = datetime.now().isoformat()
    return any(pronta(c, iso) and c["apelido"] != conta for c in _ler_contas()["contas"])


RESYNC_PRAZO_S = int(os.environ.get("ARGON_RESYNC_PRAZO_S", "240"))


def _sync_com_prazo(conta):
    """sync_cookies num processo à parte, com prazo. 30/10: rodava dentro deste processo sem limite e o Chrome do cofre
    travou 3818 s (aulasrevolution): a passada do zelador levou 75 min. Estourou = mata o processo e o Chrome filho."""
    import subprocess
    p = subprocess.Popen([sys.executable, "-X", "utf8", str(BASE / "sync_cookies.py"), conta], cwd=str(BASE),
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=0x08000000)
    try:
        saida, _ = p.communicate(timeout=RESYNC_PRAZO_S)
    except subprocess.TimeoutExpired:
        subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"], capture_output=True, creationflags=0x08000000)
        p.communicate()
        log.warning("%s: ressincronização passou de %d s — processo e Chrome derrubados", conta, RESYNC_PRAZO_S)
        return False
    if p.returncode != 0:
        log.warning("%s: sync_cookies falhou: %s", conta, (saida or b"").decode("utf-8", "replace").strip()[-200:])
    return p.returncode == 0


def ressincronizar(conta):
    """Cookies novos pelo cofre (abre o Chrome escondido, ~60-120 s). Usado pelo zelador em segundo plano; no caminho do
    pedido só quando NENHUMA outra conta está pronta."""
    with _lock_resync:
        ok = _sync_com_prazo(conta)
    _cache_tokens.pop(conta, None)
    with _trava_sessoes:
        _SESSOES.pop(conta, None)
    if ok:
        try:
            _tokens(conta, _carregar_sessao(conta))
            marcar_cookies(conta, True, novos=True)
            return True
        except Exception as e:  # noqa: BLE001
            log.warning("%s: ressincronizou mas a página ainda não trouxe SNlM0e (%s)", conta, str(e)[:80])
    marcar_cookies(conta, False)
    return False


def _abrir(conta, fixa=False):
    """Sessão pronta para uso. 29/10 (Fable, medido: 106 ressincronizações em 2 dias, mediana 78 s, p90 1 h, DENTRO do
    pedido): cookie morto agora tira a conta da fila (marcar_cookies) e o pedido passa para a próxima conta na hora
    (TrocarConta). O Chrome só entra aqui se não houver nenhuma outra conta pronta (ou conta fixa); o resto é trabalho do
    argon_zelador.py em segundo plano."""
    try:
        s = _carregar_sessao(conta)
        _tokens(conta, s)
        return s
    except (SemCookies, AuthFalhou) as e:
        log.warning("%s: %s", conta, e)
        marcar_cookies(conta, False)
        if not fixa and _outra_pronta(conta):
            raise TrocarConta(str(e)) from e
        log.warning("%s: nenhuma outra conta pronta — ressincronizando pelo cofre dentro do pedido", conta)
    if not ressincronizar(conta):
        raise AuthFalhou(f"{conta}: ressincronização pelo cofre falhou (conta deslogada?)")
    return _carregar_sessao(conta)


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


# 29/10: reuso de conversa (só o gemini_http_proxy usa; pipelines chamam sem `meta` e nada muda). Cada thread guarda
# a conta e os ids [cid, rid, rcid] da última resposta: com eles o próximo pedido CONTINUA a mesma conversa do Gemini
# (inner[2]) e manda só o turno novo, em vez do histórico inteiro.
ULTIMA = threading.local()


def _pedido(prompt, modelo, idioma, meta=None):
    """(f.req, cabeçalho jspb) do StreamGenerate; o Argon sempre com o nível de raciocínio Alto.
    meta = [cid, rid, rcid] de uma conversa existente (continua ela) ou None (conversa nova)."""
    inner = [[prompt, 0, None, None, None, None, 0], [idioma], list(meta) if meta else None]
    jspb = [1, None, None, None, MODELOS.get(modelo, MODELOS["argon"])]
    # 29/10 (dona: "todos os modelos sempre com o pensamento no máximo"): o "pro" (gweb/gemini-3.1-pro) também pensa
    # no nível Alto; antes só o Argon mandava o campo e o pro ia no padrão da conta (mais raso)
    if modelo in ("argon", "pro"):
        inner += [None] * (69 - len(inner))
        inner[68] = NIVEL_RACIOCINIO
        jspb += [None] * (12 - len(jspb))
        jspb[11] = NIVEL_RACIOCINIO
    return json.dumps([None, json.dumps(inner, ensure_ascii=False)], ensure_ascii=False), json.dumps(jspb)


def _url_headers(bl, fsid, idioma, jspb):
    """URL e cabeçalhos do StreamGenerate (iguais para pedido normal, stream e consulta da hora da volta)."""
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
    return url, headers


def _uma_chamada(sessao, conta, prompt, modelo, idioma="pt", meta=None):
    at, bl, fsid = _tokens(conta, sessao)
    freq, jspb = _pedido(prompt, modelo, idioma, meta)
    url, headers = _url_headers(bl, fsid, idioma, jspb)
    # 27/10: lido aos poucos para cortar no 1º pedaço se o Gemini não serviu o Argon (antes o Flash-Lite respondia
    # inteiro, 10-30 s jogados fora, para só então trocar de conta)
    r = sessao.post(url, data={"f.req": freq, "at": at}, headers=headers, timeout=TIMEOUT, stream=True)
    if r.status_code != 200:
        if r.status_code in (400, 401, 403):  # tokens/cookies da página vencidos: próxima vez pega de novo
            _cache_tokens.pop(conta, None)
        texto = r.text[:300]
        r.close()
        raise RuntimeError(f"StreamGenerate HTTP {r.status_code}: {texto}")
    partes, conferido = [], False
    t_ini = time.time()
    try:
        for linha in r.iter_lines(decode_unicode=True):
            if not linha:
                continue
            if time.time() - t_ini > PRAZO_TOTAL:
                raise RuntimeError(f"passou de {PRAZO_TOTAL}s (a VPS já desistiu): corto para não gastar cota")
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
    ULTIMA.info = {"conta": conta, "modelo": modelo, "meta": [cid, rid, rcid]} if cid and rid and rcid else None
    return texto


def _stream_chamada(sessao, conta, prompt, modelo, idioma="pt", meta=None):
    """Igual a _uma_chamada, mas cede (yield) os deltas de texto conforme chegam."""
    at, bl, fsid = _tokens(conta, sessao)
    freq, jspb = _pedido(prompt, modelo, idioma, meta)
    ULTIMA.info = None
    ids = [None, None, None]
    url, headers = _url_headers(bl, fsid, idioma, jspb)
    r = sessao.post(url, data={"f.req": freq, "at": at}, headers=headers, timeout=TIMEOUT, stream=True)
    # 30/10: fecha a resposta em QUALQUER saída (SemCota no 1º pedaço, cliente que desistiu = GeneratorExit, erro);
    # antes só fechava no prazo estourado e a conexão ficava presa na Session da conta
    try:
        yield from _ler_stream(r, conta, modelo, ids)
    finally:
        r.close()


def _ler_stream(r, conta, modelo, ids):
    if r.status_code != 200:
        if r.status_code in (400, 401, 403):
            _cache_tokens.pop(conta, None)
        raise RuntimeError(f"StreamGenerate HTTP {r.status_code}")
    enviado = ""
    t_ini = time.time()
    for linha in r.iter_lines(decode_unicode=True):
        if time.time() - t_ini > PRAZO_TOTAL:
            raise RuntimeError(f"passou de {PRAZO_TOTAL}s (a VPS já desistiu)")
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
            if isinstance(data, list) and len(data) > 1 and isinstance(data[1], list) and len(data[1]) >= 2:
                ids[0], ids[1] = data[1][0] or ids[0], data[1][1] or ids[1]
            if isinstance(data, list) and len(data) > 4 and data[4]:
                cand = data[4][0]
                if isinstance(cand, list) and cand and cand[0]:
                    ids[2] = cand[0]
                if isinstance(cand, list) and len(cand) > 1 and cand[1] and cand[1][0]:
                    completo = cand[1][0]
                    if len(completo) > len(enviado) and completo.startswith(enviado):
                        yield completo[len(enviado):]
                        enviado = completo
                    elif completo != enviado and len(completo) >= len(enviado):
                        # frame reescreveu o texto. 30/10: antes mandava o COMPLETO de novo (o cliente recebia o começo
                        # duplicado); o que já foi não volta, então manda só o que vem depois do maior começo em comum
                        comum = len(os.path.commonprefix([enviado, completo]))
                        log.warning("%s: Gemini reescreveu o texto no meio (%d chars enviados, %d em comum)", conta,
                                    len(enviado), comum)
                        if len(completo) > len(enviado):
                            yield completo[len(enviado):] if comum == len(enviado) else completo[max(comum, len(enviado)):]
                        enviado = completo
    if not enviado:
        raise RuntimeError("resposta vazia")
    if all(ids):
        ULTIMA.info = {"conta": conta, "modelo": modelo, "meta": list(ids)}


def perguntar_stream(prompt, conta=None, modelo="argon", idioma="pt", tentativas=6, meta=None):
    """Versão geradora: cede deltas de texto. Usa conta fixa ou a primeira pronta da fila.
    Conta sem cota do Argon (SemCota, detectada antes do 1º pedaço) sai da fila com hora de volta e a próxima
    responde; isso não gasta tentativa. Fila vazia = erro na hora (proxima_conta)."""
    erros = 0
    ignorar = set()
    while erros < tentativas:
        apelido = conta or proxima_conta(ignorar)
        mandou = False
        t0 = time.time()
        n = 0
        try:
            sessao = _abrir(apelido, fixa=bool(conta))
            t_gestao = time.time() - t0
            for delta in _stream_chamada(sessao, apelido, prompt, modelo, idioma, meta if conta else None):
                mandou = True
                n += len(delta)
                yield delta
            _salvar_sessao(apelido, sessao)
            marcar_uso(apelido, sucesso=True, segundos=time.time() - t0)
            log.info("OK %s modelo=%s %.1fs %d chars (stream, gestão %.1fs)", apelido, modelo, time.time() - t0, n, t_gestao)
            return
        except TrocarConta as e:  # 29/10: cookie morto -> próxima conta na hora, sem gastar tentativa
            log.info("%s: cookie morto, passo para a próxima (%s)", apelido, str(e)[:60])
            ignorar.add(apelido)
            if conta:
                raise
        except SemCota as e:
            log.warning("%s: %s — próxima conta", apelido, e)
            marcar_sem_cota(apelido, volta=getattr(e, "volta", None))
            if not getattr(e, "volta", None):
                _buscar_volta(apelido)
            ignorar.add(apelido)
            if conta or mandou:
                raise
        except Exception as e:
            marcar_uso(apelido, sucesso=False, erro_msg=str(e))
            # 29/10 (Fable): antes do 1º pedaço, erro = próxima conta (antes o stream não tentava de novo e o cliente
            # recebia erro direto); depois do 1º pedaço não dá para recomeçar
            if conta or mandou:
                raise
            log.warning("%s: %s — tento a próxima (%d/%d)", apelido, str(e)[:120], erros + 1, tentativas)
            ignorar.add(apelido)
            erros += 1
        finally:
            if not conta:
                soltar(apelido)
    raise RuntimeError(f"{tentativas} erros seguidos no Argon")


def perguntar(prompt, conta=None, modelo="argon", idioma="pt", tentativas=6, meta=None):
    """Pergunta ao Gemini (Argon por padrão) via HTTP puro. Retorna o texto ou None.

    Fila de contas: usa a primeira pronta; sem cota (cortada no 1º pedaço) sai com hora de volta e a próxima responde
    sem gastar tentativa; outros erros gastam tentativa. Fila vazia = RuntimeError na hora (proxima_conta).
    """
    erro_final = None
    erros = 0
    ignorar = set()
    while erros < tentativas:
        apelido = conta or proxima_conta(ignorar)
        t0 = time.time()
        try:
            sessao = _abrir(apelido, fixa=bool(conta))
            t_gestao = time.time() - t0
            texto = _uma_chamada(sessao, apelido, prompt, modelo, idioma, meta if conta else None)
            _salvar_sessao(apelido, sessao)
            if texto and texto.strip():
                marcar_uso(apelido, sucesso=True, segundos=time.time() - t0)
                log.info("OK %s modelo=%s %.1fs %d chars (gestão %.1fs)", apelido, modelo, time.time() - t0, len(texto), t_gestao)
                return texto
            marcar_uso(apelido, sucesso=False, erro_msg="resposta vazia")
            erro_final = "resposta vazia"
            erros += 1
        except TrocarConta as e:
            log.info("%s: cookie morto, passo para a próxima (%s)", apelido, str(e)[:60])
            ignorar.add(apelido)
            erro_final = str(e)
        except SemCota as e:
            log.warning("%s: %s — próxima conta (%.1fs)", apelido, e, time.time() - t0)
            marcar_sem_cota(apelido, volta=getattr(e, "volta", None))
            if not getattr(e, "volta", None):
                _buscar_volta(apelido)
            ignorar.add(apelido)
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
