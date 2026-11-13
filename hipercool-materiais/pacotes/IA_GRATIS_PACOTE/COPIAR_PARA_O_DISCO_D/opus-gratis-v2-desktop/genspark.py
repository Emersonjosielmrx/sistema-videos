# -*- coding: utf-8 -*-
r"""genspark.py — pool de contas do Genspark para falar com o Claude Opus 5.5 de graça.

O Genspark dá 100 créditos/dia por conta Google (renova por dia) e o chat já vem com o
Claude Opus 5.5 selecionado; uma mensagem curta custa ~3 créditos (~30 msg/dia por conta).
Com as ~65 contas vivas do cofre isso dá ~2.000 mensagens Opus 5.5/dia.

Mesma ideia do gemini-argo e do "sonnet web": um POOL de contas com FILA (a 1ª pronta responde),
cota por conta, conta sem cota sai da fila até o dia virar, e o navegador do cofre
(D:\logins-google\cofre.py) cuida dos perfis/portas (1 Chrome por conta, compartilhado com os
outros projetos).

O Genspark NÃO tem cadastro próprio: entra só por "Entrar com Google" (OAuth). Como cada conta
do cofre já está logada no Google, o "cadastro" é um clique por conta, feito uma vez
(`python genspark.py login`), e persiste no perfil.

Uso como módulo:
    from genspark import perguntar
    resposta = perguntar("Quanto é 17 x 23?")            # 1ª conta pronta da fila
    resposta = perguntar("...", conta="conta_exemplo")       # conta fixa

CLI:
    python genspark.py "Quanto é 17 x 23?"               # pergunta (fila de contas)
    python genspark.py --conta conta_exemplo "oi"            # conta fixa
    python genspark.py semear                            # põe as contas do cofre na fila
    python genspark.py login [--todas] [--conta X]       # faz o login Google no Genspark (1 por 1)
    python genspark.py checar [--conta X]                # confere login + modelo sem gastar crédito
    python genspark.py listar                            # estado da fila (créditos, login, cota)
"""
import json
import logging
import os
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
import cofre  # noqa: E402

BASE = Path(__file__).resolve().parent   # a própria pasta do projeto (portável: desktop, v2, pc1)
CONTAS = BASE / "contas_genspark.json"
LOG_FILE = BASE / "genspark.log"
PRINTS = BASE / "prints"

CHAT_URL = "https://www.genspark.ai/agents?type=ai_chat"
MODELO_PADRAO = "Claude Opus 5.5"

CREDITOS_DIA = int(os.environ.get("GENSPARK_CREDITOS_DIA", "100"))   # o Genspark dá 100/dia por conta
CUSTO_MSG = int(os.environ.get("GENSPARK_CUSTO", "3"))              # ~3 créditos por mensagem curta (medido 30/10)
TIMEOUT_RESPOSTA = int(os.environ.get("GENSPARK_TIMEOUT", "240"))
ESTAVEL_S = 6          # resposta parada por tanto tempo = terminou
DESBLOQUEIO_MIN = 30   # conta bloqueada por 3 erros volta depois disso

from logging.handlers import RotatingFileHandler  # noqa: E402

_h = RotatingFileHandler(str(LOG_FILE), maxBytes=5_000_000, backupCount=5, encoding="utf-8")
_h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S"))
logging.basicConfig(level=logging.INFO, handlers=[_h])
log = logging.getLogger("genspark")

# Textos ESPECÍFICOS de crédito esgotado. NÃO pôr termos genéricos ("upgrade", "assine", "plus"): a UI grátis
# do Genspark mostra um botão fixo de upgrade o tempo todo, e ele cairia em document.body.innerText derrubando
# conta sã como se fosse paywall. Só frases que de fato indicam cota acabada.
PAYWALL = ["crédito insuficiente", "créditos insuficientes", "sem créditos", "créditos esgotados",
           "insufficient credits", "you've run out of credits", "run out of credits", "no credits left",
           "créditos diários esgotados", "limite diário de créditos", "daily credit limit",
           "você atingiu o limite", "limite de créditos atingido"]
# conta sem acesso ao Opus no plano grátis (31/10: conta_exemplo) — vem COMO resposta, então checa o texto da resposta
SEM_MODELO = ["benefício da assinatura", "faça upgrade para desbloque", "upgrade to unlock", "available on paid plans"]


class SemCota(Exception):
    """A conta ficou sem crédito (paywall) — sai da fila até o dia virar."""


class SemOpus(SemCota):
    """A conta não tem o Opus no plano grátis — sai da fila de vez (c["opus"] = False)."""


def marcar_opus(apelido, tem):
    with _TRAVA, _trava_arq():
        dados = _ler()
        c = _conta(dados, apelido)
        if c:
            c["opus"] = tem
            _gravar(dados)


class NaoLogado(Exception):
    """A conta não está logada no Genspark — precisa de `python genspark.py login`."""


# ─────────────────────────── registro de contas ────────────────────────────
_TRAVA = threading.RLock()        # serializa as threads DESTE processo
_EM_USO = {}  # apelido -> pedidos em andamento neste processo
_LOCK_ARQ = CONTAS.with_suffix(".lock")
_LOCKS_CONTA = {}                 # apelido -> Lock (serializa o uso da MESMA conta neste processo)
# Chrome QUENTE: fica aberto entre turnos (abrir+carregar o SPA custava ~10-15 s por pedido). Fecha após QUENTE_MIN
# parado; no máximo QUENTE_MAX abertos (RAM). apelido -> {"porta", "proc", "ultimo"}
_QUENTES = {}
QUENTE_MIN = int(os.environ.get("GENSPARK_QUENTE_MIN", "10"))
QUENTE_MAX = int(os.environ.get("GENSPARK_QUENTE_MAX", "3"))
_LOCKS_LOCK = threading.Lock()


class _trava_arq:
    """Lock de arquivo entre PROCESSOS (o _TRAVA/RLock só vale dentro do processo): protege o ciclo
    ler-modifica-grava do contas_genspark.json quando o genspark_http.py e um CLI rodam ao mesmo tempo
    (sem ele, uma gravação sobrescreve a outra inteira — lost update). Spin curto; rouba o lock se ficar
    preso >30 s (processo morto); se mesmo assim não conseguir, segue (o RLock ainda protege no processo),
    para nunca travar o pedido."""

    def __enter__(self):
        self.fd = None
        fim = time.time() + 10
        while time.time() < fim:
            try:
                self.fd = os.open(str(_LOCK_ARQ), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                return self
            except FileExistsError:
                try:
                    if time.time() - os.path.getmtime(_LOCK_ARQ) > 30:
                        os.unlink(_LOCK_ARQ)
                        continue
                except OSError:
                    pass
                time.sleep(0.05)
        return self

    def __exit__(self, *a):
        if self.fd is not None:
            try:
                os.close(self.fd)
                os.unlink(_LOCK_ARQ)
            except OSError:
                pass


def _lock_conta(apelido):
    """Lock por conta (neste processo): duas threads nunca dirigem o MESMO Chrome/aba ao mesmo tempo."""
    with _LOCKS_LOCK:
        lk = _LOCKS_CONTA.get(apelido)
        if lk is None:
            lk = _LOCKS_CONTA[apelido] = threading.Lock()
        return lk


def _ler():
    if CONTAS.exists():
        return json.loads(CONTAS.read_text(encoding="utf-8"))
    return {"_leia": "Pool de contas do Genspark (Opus 5.5). Veja genspark.py.", "contas": []}


def _gravar(dados):
    """Gravação atômica tolerante a concorrência (molde do gemini_argon: proxy multi-thread + CLI ao mesmo tempo)."""
    tmp = CONTAS.with_suffix(f".{os.getpid()}.{threading.get_ident()}.tmp")
    tmp.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    for i in range(20):
        try:
            os.replace(tmp, CONTAS)
            return
        except PermissionError:
            time.sleep(0.05 * (i + 1))
    tmp.unlink(missing_ok=True)
    log.warning("contas_genspark.json preso por outro processo: estado desta chamada não gravado")


def _conta(dados, apelido):
    for c in dados["contas"]:
        if c["apelido"] == apelido:
            return c
    return None


def _virar_dia(c, hoje):
    """Se é um dia novo, renova os créditos da conta e tira ela da espera de cota."""
    if c.get("data_cota") != hoje:
        c["data_cota"] = hoje
        c["creditos"] = CREDITOS_DIA
        c.pop("sem_cota_ate", None)
        return True
    return False


def pronta(c, hoje, agora_iso):
    if not c.get("logado"):
        return False
    if c.get("bloqueada"):
        return False
    if c.get("opus") is False:  # sem Opus no plano grátis (zelador_genspark.py testou): nunca serve
        return False
    cred = CREDITOS_DIA if c.get("data_cota") != hoje else c.get("creditos", CREDITOS_DIA)
    if cred < CUSTO_MSG:
        return False
    if c.get("sem_cota_ate") and agora_iso < c["sem_cota_ate"] and c.get("data_cota") == hoje:
        return False
    return True


def proxima_conta(ignorar=()):
    """Apelido da 1ª conta pronta da fila (logada, com crédito hoje, não bloqueada), a menos ocupada em empate.
    Desbloqueia quem errou há mais de DESBLOQUEIO_MIN. Fila vazia = RuntimeError na hora."""
    with _TRAVA, _trava_arq():
        dados = _ler()
        if not dados["contas"]:
            raise RuntimeError("Nenhuma conta na fila. Rode: python genspark.py semear  e  python genspark.py login")
        agora = datetime.now()
        hoje = agora.date().isoformat()
        iso = agora.isoformat()
        mudou = False
        for c in dados["contas"]:
            mudou |= _virar_dia(c, hoje)
            if c.get("bloqueada") and c.get("ultimo_uso") and \
                    agora - datetime.fromisoformat(c["ultimo_uso"]) > timedelta(
                        minutes=c.get("espera_min", DESBLOQUEIO_MIN)):
                c["bloqueada"] = False
                c["erros_seguidos"] = 0
                mudou = True
        if mudou:
            _gravar(dados)
        prontas = [c["apelido"] for c in dados["contas"] if pronta(c, hoje, iso) and c["apelido"] not in ignorar]
        if not prontas:
            com_login = [c for c in dados["contas"] if c.get("logado")]
            if not com_login:
                raise RuntimeError("Nenhuma conta logada no Genspark. Rode: python genspark.py login")
            volta = min((c["sem_cota_ate"] for c in dados["contas"] if c.get("sem_cota_ate")), default=None)
            raise RuntimeError("Nenhuma conta com crédito do Genspark agora"
                               + (f" (a 1ª renova {volta[:16]})" if volta else " (todas sem cota hoje)"))
        # só contas LIVRES (nenhum pedido em curso): duas threads nunca pegam a mesma conta/aba
        livres = [a for a in prontas if _EM_USO.get(a, 0) == 0]
        if not livres:
            raise RuntimeError("Todas as contas prontas estão ocupadas por outro pedido agora")
        # Chrome já aberto (quente) primeiro: poupa ~10-15 s; depois a de mais crédito (espalha o gasto)
        cred = {c["apelido"]: (c.get("creditos", CREDITOS_DIA) if c.get("data_cota") == hoje else CREDITOS_DIA)
                for c in dados["contas"]}
        escolhida = min(livres, key=lambda a: (a not in _QUENTES, -cred.get(a, 0)))
        _EM_USO[escolhida] = _EM_USO.get(escolhida, 0) + 1
        return escolhida


def soltar(apelido):
    with _TRAVA:
        if _EM_USO.get(apelido, 0) > 0:
            _EM_USO[apelido] -= 1


def marcar_uso(apelido, sucesso=True, custo=CUSTO_MSG, erro_msg=None, segundos=None):
    with _TRAVA, _trava_arq():
        dados = _ler()
        c = _conta(dados, apelido)
        if not c:
            return
        hoje = datetime.now().date().isoformat()
        _virar_dia(c, hoje)
        c["ultimo_uso"] = datetime.now().isoformat(timespec="minutes")
        st = c.setdefault("stats", {"ok": 0, "erros": 0, "seg_total": 0.0, "creditos_gastos": 0})
        if sucesso:
            c["erros_seguidos"] = 0
            c["bloqueada"] = c["bloqueada_antes"] = False
            c["creditos"] = max(0, c.get("creditos", CREDITOS_DIA) - custo)
            st["ok"] += 1
            st["creditos_gastos"] = st.get("creditos_gastos", 0) + custo
            if segundos:
                st["seg_total"] = round(st["seg_total"] + segundos, 1)
            if c["creditos"] < CUSTO_MSG:  # acabou a cota do dia
                c["sem_cota_ate"] = _amanha_cedo()
                log.info("Conta %s sem crédito pelo resto do dia (renova %s)", apelido, c["sem_cota_ate"][:16])
        else:
            st["erros"] += 1
            c["erros_seguidos"] = c.get("erros_seguidos", 0) + 1
            c["ultimo_erro"] = (erro_msg or "")[:120]
            if c["erros_seguidos"] >= 3:
                # espera crescente (molde: gemini_argon.marcar_sem_cota): 15 → 30 → 60 → ... até 3 h; zera no sucesso
                c["espera_min"] = min(180, c["espera_min"] * 2) if c.get("bloqueada_antes") else 15
                c["bloqueada"] = c["bloqueada_antes"] = True
                log.warning("Conta %s bloqueada %d min após 3 erros: %s", apelido, c["espera_min"], erro_msg)
        _gravar(dados)


def marcar_sem_cota(apelido):
    with _TRAVA, _trava_arq():
        dados = _ler()
        c = _conta(dados, apelido)
        if c:
            hoje = datetime.now().date().isoformat()
            _virar_dia(c, hoje)      # se o dia virou mesmo, renova; senão garante data_cota=hoje
            c["data_cota"] = hoje    # FIXA hoje: sem isto o _virar_dia seguinte veria data antiga e renovaria a cota, apagando o paywall no mesmo dia
            c["creditos"] = 0
            c["sem_cota_ate"] = _amanha_cedo()
            log.warning("Conta %s: paywall do Genspark, fora da fila até %s", apelido, c["sem_cota_ate"][:16])
            _gravar(dados)


def marcar_logado(apelido, logado, detalhe=None):
    with _TRAVA, _trava_arq():
        dados = _ler()
        c = _conta(dados, apelido)
        if c:
            c["logado"] = bool(logado)
            c["login_checado"] = datetime.now().isoformat(timespec="minutes")
            if detalhe:
                c["login_detalhe"] = detalhe[:120]
            _gravar(dados)


def _amanha_cedo():
    d = datetime.now() + timedelta(days=1)
    return d.replace(hour=0, minute=5, second=0, microsecond=0).isoformat(timespec="minutes")


def semear(so_vivas=True):
    """Põe as contas Google do cofre na fila (pula as de Instagram, que não têm Google). logado=None até o login."""
    reg = json.loads((Path(cofre.REGISTRO)).read_text(encoding="utf-8"))
    with _TRAVA, _trava_arq():
        dados = _ler()
        existentes = {c["apelido"] for c in dados["contas"]}
        novas = 0
        for email, e in reg["contas"].items():
            if e.get("tipo") == "instagram":
                continue
            if so_vivas and e.get("google") == "morto":
                continue
            apelido = e.get("apelido") or email.split("@")[0]
            if apelido in existentes:
                continue
            dados["contas"].append({
                "email": email, "apelido": apelido, "logado": None,
                "creditos": CREDITOS_DIA, "data_cota": None, "bloqueada": False,
                "erros_seguidos": 0, "ultimo_uso": None,
            })
            novas += 1
        _gravar(dados)
    print(f"Semeado: +{novas} contas (total {len(dados['contas'])}). "
          f"Agora rode: python genspark.py login  (faz o 'Entrar com Google' em cada uma).")


# ─────────────────────────── navegador ─────────────────────────────────────
_JS_ESTADO = r"""(() => {
  const inp = document.querySelector('textarea.search-input, textarea.j-search-input');
  const modeloBtn = [...document.querySelectorAll('button')].find(b => /claude|opus|gpt|gemini|sonnet/i.test(b.innerText||''));
  const ans = [...document.querySelectorAll('.answer-markdown')];
  // innerText perde as cercas ``` e traz o "Copy" do botao: refaz o markdown dos blocos de codigo pelo DOM
  const md = (el) => [...el.childNodes].map(n => {
    if (n.nodeType === 3) return n.textContent;
    if (n.nodeType !== 1) return '';
    const pres = n.tagName === 'PRE' ? [n] : [];
    if (!pres.length && !n.querySelector('pre')) return (n.innerText || '') + '\n';
    if (!pres.length) return md(n) + '\n';
    const code = n.querySelector('code') || n;
    const lang = ((code.className || '').match(/language-([\w-]+)/) || [])[1] || '';
    const corpo = [...code.childNodes].filter(c => !(c.nodeType === 1 && c.matches('button'))).map(c => c.textContent).join('');
    return '\n```' + lang + '\n' + corpo.replace(/\n$/, '') + '\n```\n';
  }).join('').replace(/\n{3,}/g, '\n\n');
  const ultima = ans.length ? md(ans[ans.length-1]).trim() : '';
  const parar = [...document.querySelectorAll('button')].some(b => b.offsetParent!==null &&
      /parar|stop|interromper/i.test((b.getAttribute('aria-label')||b.innerText||'')));
  // botao de login visivel = nao logado (inclui "Iniciar sessão" do Genspark pt-BR, que fica dentro do menu)
  const login = [...document.querySelectorAll('button,a')].some(b => b.offsetParent!==null &&
      /entrar|sign ?in|log ?in|fazer login|iniciar sess/i.test((b.innerText||'').trim()) && (b.innerText||'').length < 30);
  const corpo = (document.body.innerText||'').toLowerCase();
  // modal de login: "Entrar ou cadastrar-se" / "Continuar com Google" sobre o chat (aparece ao enviar se deslogada)
  const modal = /entrar ou cadastrar|continuar com o? google/i.test(corpo);
  return {temInput: !!inp, modelo: modeloBtn ? (modeloBtn.innerText||'').trim().slice(0,40) : null,
          resposta: ultima, n: ans.length, gerando: parar, temLogin: login, modal: modal, corpo: corpo.slice(0, 4000)};
})()"""


_ESTADO_VAZIO = {"temInput": False, "modelo": None, "resposta": "", "gerando": False, "temLogin": False, "corpo": ""}


def _estado(pg):
    try:
        return pg.evaluate(_JS_ESTADO)
    except Exception:  # noqa: BLE001  (página ainda navegando/sem document): estado vazio, o chamador volta a tentar
        return dict(_ESTADO_VAZIO)


def _front(pg):
    try:
        pg.bring_to_front()  # aba de fundo não desenha; traz pra frente
    except Exception:  # noqa: BLE001
        pass
    return pg


def _url(pg):
    try:
        return pg.url or ""
    except Exception:  # noqa: BLE001
        return ""


def _pagina(ctx):
    """Dá uma aba DEDICADA ao Genspark, sem sequestrar a aba de trabalho de outro projeto (o cofre compartilha o
    mesmo Chrome entre projetos). Preferência: (1) aba já no genspark.ai; (2) aba em branco (o cofre abre o Chrome
    com about:blank); (3) abre uma aba nova. Não pega uma aba arbitrária que pode ser de outro projeto."""
    paginas = ctx.pages
    for pg in paginas:
        if "genspark.ai" in _url(pg):
            return _front(pg)
    for pg in paginas:
        u = _url(pg)
        if u in ("", "about:blank") or u.startswith("chrome://newtab"):
            return _front(pg)
    return _front(ctx.new_page())


def _tem_paywall(corpo):
    return any(p in corpo for p in PAYWALL)


def _sessao(pg):
    """E-mail da conta logada no Genspark (via /api/is_login, chamado de dentro da página), "" se visitante,
    None se não deu para saber. Usado pelos modos sem-navegador (genspark_pagina / genspark_http_puro) — a tela
    é igual para visitante e logado, então o teste por DOM dava falso positivo. (Desktop 31/10.)"""
    try:
        d = pg.evaluate("fetch('/api/is_login', {credentials: 'include'}).then(r => r.json())")
        return ((d or {}).get("data") or {}).get("cogen_email") or ""
    except Exception as e:  # noqa: BLE001
        log.warning("is_login falhou: %s", str(e)[:80])
        return None


ESPERA_SPA = int(os.environ.get("GENSPARK_ESPERA_SPA", "120"))  # quanto esperar o SPA montar (máquina carregada demora)


def _ir_chat(pg, url=None):
    """Abre uma conversa NOVA (reseta pro Opus 5.5 padrão) e espera o campo de texto aparecer.
    Não depende do `domcontentloaded` (sob carga pesada da máquina ele não dispara em 60 s — o nav.py chega a levar
    ~80 s): navega com `commit` (só precisa da resposta do servidor) e faz polling do campo por ESPERA_SPA segundos."""
    try:
        pg.bring_to_front()  # aba de fundo não desenha; traz pra frente antes de navegar
    except Exception:  # noqa: BLE001
        pass
    # url = conversa a continuar (reuso); a aba quente já nela não recarrega
    if not (url and _url(pg) == url):
        try:
            pg.goto(url or CHAT_URL, wait_until="commit", timeout=60000)
        except Exception as e:  # noqa: BLE001  (até o commit pode demorar sob rede saturada): segue pro polling
            log.warning("goto demorou/estourou (%s); sigo pelo polling do campo", str(e)[:70])
    prazo = time.time() + ESPERA_SPA
    st = dict(_ESTADO_VAZIO)
    while time.time() < prazo:
        st = _estado(pg)
        if st["temInput"] or (st["temLogin"] and not st["temInput"]):
            return st
        time.sleep(2)
    return st


def _garantir_modelo(pg, alvo=MODELO_PADRAO):
    """Confere se o modelo selecionado é o Opus 5.5; se não, tenta trocar no seletor. Best-effort."""
    st = _estado(pg)
    if st.get("modelo") and "opus" in st["modelo"].lower():
        return True
    try:
        import re as _re
        btn = pg.locator("button").filter(has_text=_re.compile("Opus|Claude", _re.I)).first
        btn.click(timeout=4000)
        time.sleep(1)
        op = pg.get_by_text("Opus 5.5", exact=False).first
        op.click(timeout=4000)
        time.sleep(1)
        log.info("Modelo trocado para Opus 5.5")
        return True
    except Exception as e:  # noqa: BLE001
        log.warning("Não confirmei o modelo Opus 5.5 (segue no padrão da conta): %s", str(e)[:80])
        return False


def _enviar(pg, texto):
    campo = pg.locator("textarea.search-input, textarea.j-search-input").first
    campo.click(timeout=10000)
    time.sleep(0.2)
    pg.keyboard.insert_text(texto)
    time.sleep(0.4 + len(texto) / 150000)
    pg.keyboard.press("Enter")
    log.info("Pergunta enviada (%d chars)", len(texto))


MODELO_API = "claude-opus-5-5"  # ai_chat_model no corpo do ask_proxy


def _coletar(pg, timeout_s=TIMEOUT_RESPOSTA, rede=None):
    """rede["fim"] = hora em que o ask_proxy terminou (ver _uma): aí basta o texto parar por 1 s."""
    inicio = time.time()
    ultimo, estavel_desde, gerando = "", None, True
    rede = rede if rede is not None else {}
    time.sleep(1)
    while time.time() - inicio < timeout_s:
        st = _estado(pg)
        if _tem_paywall(st["corpo"]) and len(st["resposta"]) < 40:
            raise SemCota("paywall do Genspark na resposta")
        if st.get("modal") and not st["resposta"]:  # pediu login ao enviar: falha já, não espera 240 s
            raise NaoLogado("modal de login apareceu ao enviar")
        txt, gerando = st["resposta"], st["gerando"]
        if st.get("n", 0) <= rede.get("n_antes", 0):  # conversa reaproveitada: a última resposta ainda é a antiga
            txt = ""
        if txt and len(txt) < 200 and any(p in txt.lower() for p in SEM_MODELO):
            raise SemOpus("conta sem acesso ao Opus (pede assinatura)")
        if txt and txt != ultimo:
            ultimo, estavel_desde = txt, time.time()
        elif txt and estavel_desde and (
                (rede.get("fim") and time.time() - max(estavel_desde, rede["fim"]) > 1)
                or (not gerando and time.time() - estavel_desde > ESTAVEL_S)):
            log.info("Resposta completa (%d chars, %.1fs%s)", len(txt), time.time() - inicio,
                     ", fim pela rede" if rede.get("fim") else "")
            return txt
        time.sleep(0.7 if rede.get("fim") else 1.5)
    # Timeout: só devolve se a resposta já estava ESTÁVEL (não gerando) — senão é parcial e vale como erro,
    # para o chamador não tratar meia resposta como final (marcaria sucesso e creditaria a conta).
    if ultimo and not gerando:
        log.warning("Timeout, mas resposta estável; devolvo (%d chars)", len(ultimo))
        return ultimo
    raise RuntimeError(f"timeout de {timeout_s}s com resposta incompleta ({len(ultimo)} chars)")


def _menu_conta(pg):
    """Abre o menu do rodapé e devolve (logado, créditos). Prova real (30/10): o visitante vê o mesmo chat e o
    textarea; só o menu diferencia — logada = e-mail + "Créditos: N" + "Terminar sessão"; visitante = "Iniciar
    sessão". (None, None) se o menu não abriu (SPA lento): o chamador não deve concluir nada."""
    import re as _re
    for tentativa in range(3):  # logo após o campo aparecer o menu às vezes ainda não responde ao clique
        time.sleep(2)
        try:
            pg.locator(".sidebar-footer .trigger").locator("visible=true").first.click(timeout=8000)
            time.sleep(1.5)
            corpo = " ".join((pg.evaluate("() => document.body.innerText || ''") or "").split())
            pg.keyboard.press("Escape")
        except Exception as e:  # noqa: BLE001
            log.warning("menu da conta não abriu (%d/3): %s", tentativa + 1, str(e)[:80])
            continue
        m = _re.search(r"Cr[ée]ditos:\s*([\d.,]+)", corpo)
        cred = int(_re.sub(r"[.,]", "", m.group(1))) if m else None
        # com a máquina carregada o Genspark às vezes desenha as chaves de tradução cruas (components.menu.sign-in)
        if "Terminar sessão" in corpo or "Sign out" in corpo or "Log out" in corpo or "sign-out" in corpo or m:
            return True, cred
        if "Iniciar sessão" in corpo or "Sign in" in corpo or "Log in" in corpo or "menu.sign-in" in corpo:
            return False, None
    log.warning("menu da conta sem resposta clara após 3 tentativas")
    return None, None


def marcar_creditos(apelido, creditos):
    """Grava o saldo REAL lido no menu (no lugar da estimativa)."""
    with _TRAVA, _trava_arq():
        dados = _ler()
        c = _conta(dados, apelido)
        if c:
            hoje = datetime.now().date().isoformat()
            _virar_dia(c, hoje)
            c["data_cota"] = hoje
            c["creditos"] = creditos
            c["creditos_lidos_em"] = datetime.now().isoformat(timespec="minutes")
            if creditos < CUSTO_MSG:
                c["sem_cota_ate"] = _amanha_cedo()
            _gravar(dados)


def _logado(pg, apelido=None):
    """True/False se a conta está logada no Genspark, pelo menu do rodapé (ver _menu_conta). Grava os créditos reais."""
    st = _ir_chat(pg)
    if not st["temInput"] and not st["temLogin"]:
        return False
    logado, cred = _menu_conta(pg)
    if logado and apelido and cred is not None:
        marcar_creditos(apelido, cred)
    return bool(logado)


# ─────────────────────────── login (1 por 1) ───────────────────────────────
import re as _re_mod  # noqa: E402
_re_google = _re_mod.compile(r"^\s*(continuar com google|components\.\S*google\S*)\s*$", _re_mod.I)

def _tentar_login_google(pg):
    """Clica em Entrar -> Continuar com Google e tenta escolher a (única) conta do perfil. Best-effort.
    No Genspark pt-BR o "Iniciar sessão" fica dentro do menu do rodapé: abre o menu antes."""
    try:
        pg.locator(".sidebar-footer .trigger").locator("visible=true").first.click(timeout=8000)
        time.sleep(1.5)
    except Exception:  # noqa: BLE001
        pass
    for txt in ["Iniciar sessão", "components.menu.sign-in", "Entrar", "Fazer login", "Sign in", "Log in", "Login"]:
        try:
            b = pg.get_by_text(txt, exact=False).locator("visible=true").first
            if b.is_visible(timeout=2500):
                b.click()
                time.sleep(2.5)
                break
        except Exception:  # noqa: BLE001
            continue
    for txt in ["Continuar com Google", "Continuar com o Google", "Continue with Google", "Entrar com o Google",
                "Sign in with Google"]:
        try:
            b = pg.get_by_text(txt, exact=False).locator("visible=true").first
            if b.is_visible(timeout=5000):
                b.click()
                time.sleep(3)
                break
        except Exception:  # noqa: BLE001
            continue
    else:  # sem tradução: o botão do Google é o 1º do modal com "google" no texto ou na chave
        try:
            pg.locator("button, [role=button], div").filter(has_text=_re_google).locator("visible=true").last.click(timeout=5000)
            time.sleep(3)
        except Exception:  # noqa: BLE001
            pass
    # O seletor de conta do Google costuma vir com 1 conta só no perfil: clicar nela. Pelo TEXTO do e-mail
    # (o antigo div:has-text("@gmail.com") pegava a div da página inteira e o clique caía no vazio).
    import re as _re
    # Depois vem a tela de consentimento (/signin/oauth/id: "Continuar"). Nela o e-mail é um chip que abre a
    # troca de conta — clicar nele (31/10) deixava a tela parada. Só clica no e-mail na escolha de conta.
    time.sleep(3)
    for _ in range(12):
        u = _url(pg)
        log.info("login google: %s", u[:90])
        if "accounts.google" not in u:
            break
        try:
            feito = False
            for txt in ["Continuar", "Continue", "Permitir", "Allow"]:
                b = pg.get_by_role("button", name=txt, exact=True).first
                if b.is_visible(timeout=1000):
                    b.click()
                    feito = True
                    break
            if not feito and "/oauth/id" not in u:
                linha = pg.locator("[data-identifier], [data-email]").locator("visible=true").first
                if linha.is_visible(timeout=1500):
                    linha.click()
                else:
                    cont = pg.get_by_text(_re.compile(r"^\S+@gmail\.com$")).locator("visible=true").first
                    if cont.is_visible(timeout=1500):
                        cont.click()
        except Exception:  # noqa: BLE001
            pass
        time.sleep(3)
    time.sleep(4)


def login(conta=None, todas=False, visivel=False):
    """Faz o 'Entrar com Google' no Genspark para 1 conta, ou varre a fila (logado in (None, False))."""
    from playwright.sync_api import sync_playwright
    dados = _ler()
    if conta:
        alvos = [c for c in dados["contas"] if c["apelido"] == conta or c["email"] == conta]
    elif todas:
        alvos = list(dados["contas"])
    else:
        alvos = [c for c in dados["contas"] if not c.get("logado")]
    if not alvos:
        print("Nada para logar (use --todas para refazer todas, ou semear primeiro).")
        return
    print(f"Login no Genspark em {len(alvos)} conta(s)...")
    for c in alvos:
        apelido = c["apelido"]
        try:
            porta, proc = cofre.abrir(apelido, url="about:blank", visivel=visivel)
        except Exception as e:  # noqa: BLE001
            print(f"  {apelido:32} ERRO ao abrir Chrome: {str(e)[:60]}")
            marcar_logado(apelido, False, f"abrir: {e}")
            continue
        br = None
        try:
            with sync_playwright() as pw:
                br = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}", timeout=45000)
                pg = _pagina(br.contexts[0])
                if _logado(pg, apelido):
                    marcar_logado(apelido, True, "já logada (menu)")
                    print(f"  {apelido:32} JÁ LOGADA")
                else:
                    _tentar_login_google(pg)
                    pg = _pagina(br.contexts[0])  # o OAuth pode voltar noutra aba
                    ok = _logado(pg, apelido)
                    marcar_logado(apelido, ok, None if ok else "login automático não concluiu")
                    print(f"  {apelido:32} {'LOGOU' if ok else 'FALHOU (logar à mão: cofre.py logar '+apelido+')'}")
        except Exception as e:  # noqa: BLE001
            marcar_logado(apelido, False, str(e))
            print(f"  {apelido:32} ERRO: {str(e)[:60]}")
        finally:
            cofre.fechar(proc, br, apelido)


def checar(conta=None):
    """Confere login + modelo de 1 conta (ou de todas as logadas) sem gastar crédito."""
    from playwright.sync_api import sync_playwright
    dados = _ler()
    alvos = [c for c in dados["contas"] if (not conta) or c["apelido"] == conta or c["email"] == conta]
    if conta is None:
        alvos = [c for c in alvos if c.get("logado")]
    for c in alvos:
        apelido = c["apelido"]
        porta, proc = cofre.abrir(apelido, url="about:blank")
        br = None
        try:
            with sync_playwright() as pw:
                br = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}", timeout=45000)
                pg = _pagina(br.contexts[0])
                logado = _logado(pg, apelido)
                marcar_logado(apelido, logado, "menu" if logado else "menu: Iniciar sessão")
                cred = (_conta(_ler(), apelido) or {}).get("creditos")
                print(f"  {apelido:32} login={'sim' if logado else 'NÃO':3}  créditos={cred if logado else '-'}")
        except Exception as e:  # noqa: BLE001
            print(f"  {apelido:32} ERRO: {str(e)[:60]}")
        finally:
            cofre.fechar(proc, br, apelido)


# ─────────────────────────── pergunta principal ────────────────────────────
def _fechar_quente(apelido):
    q = _QUENTES.pop(apelido, None)
    if q:
        cofre.fechar(q["proc"], None, apelido)
        if q["proc"] is None:  # aberto por outro projeto: não é nosso
            return
        log.info("Chrome quente de %s fechado", apelido)


def _faxina_quentes():
    """Fecha os Chromes quentes parados há mais de QUENTE_MIN (roda numa thread)."""
    while True:
        time.sleep(60)
        with _TRAVA:
            parados = [a for a, q in _QUENTES.items()
                       if _EM_USO.get(a, 0) == 0 and time.time() - q["ultimo"] > QUENTE_MIN * 60]
        for a in parados:
            with _lock_conta(a):
                _fechar_quente(a)


def _abrir_quente(apelido, visivel=False):
    """(porta, proc) do Chrome da conta, reaproveitando o que já está aberto e vivo."""
    q = _QUENTES.get(apelido)
    if q and cofre._cdp_vivo(q["porta"]):
        return q["porta"], q["proc"]
    _QUENTES.pop(apelido, None)
    with _TRAVA:  # abre espaço: fecha o quente parado há mais tempo
        sobra = sorted((q["ultimo"], a) for a, q in _QUENTES.items() if _EM_USO.get(a, 0) == 0)
        excesso = len(_QUENTES) - QUENTE_MAX + 1
    for _, a in sobra[:max(0, excesso)]:
        with _lock_conta(a):
            _fechar_quente(a)
    porta, proc = cofre.abrir(apelido, url="about:blank", visivel=visivel)
    _QUENTES[apelido] = {"porta": porta, "proc": proc, "ultimo": time.time()}
    if not getattr(_faxina_quentes, "rodando", False):
        _faxina_quentes.rodando = True
        threading.Thread(target=_faxina_quentes, daemon=True, name="faxina-quentes").start()
    return porta, proc


ULTIMA = threading.local()  # .info = {"conta", "url"} da última resposta desta thread (reuso de conversa)


def _uma(apelido, prompt, visivel=False, print_dir=None, conversa=None):
    from playwright.sync_api import sync_playwright
    with _lock_conta(apelido):  # duas threads nunca dirigem o MESMO Chrome/aba da mesma conta
        porta, proc = _abrir_quente(apelido, visivel=visivel)
        br = None
        try:
            with sync_playwright() as pw:
                br = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}", timeout=45000)
                pg = _pagina(br.contexts[0])
                st = _ir_chat(pg, conversa)
                if not (st["temInput"] and not st["temLogin"]):
                    if _tem_paywall(st["corpo"]):
                        raise SemCota("sem cota (paywall) ao abrir")
                    if st["temLogin"]:   # botão de login visível = deslogada de verdade
                        marcar_logado(apelido, False, "botão de login visível")
                        raise NaoLogado(f"{apelido} não está logada no Genspark")
                    # nem campo nem login: o SPA não montou (lentidão/transitório) — NÃO marca logado=False
                    # (senão uma lentidão momentânea tirava uma conta boa do pool até alguém relogar à mão)
                    raise RuntimeError(f"{apelido}: o chat do Genspark não montou (SPA lento/transitório)")
                q = _QUENTES.get(apelido, {})
                if not q.get("menu_ok"):  # menu (prova de login + saldo) só na 1ª vez de cada Chrome quente
                    logado, cred = _menu_conta(pg)  # o textarea engana: visitante também vê
                    if logado is False:
                        marcar_logado(apelido, False, "menu: Iniciar sessão")
                        raise NaoLogado(f"{apelido} não está logada no Genspark")
                    if cred is not None:
                        marcar_creditos(apelido, cred)
                        if cred < CUSTO_MSG:
                            raise SemCota(f"site mostra {cred} créditos")
                    if logado:
                        q["menu_ok"] = True
                # O pedido do site (/api/agent/ask_proxy) diz o modelo e o fim dele marca o fim da resposta:
                # substitui o clique no seletor de modelo (sempre estourava 4 s) e os ~9 s de espera por texto parado.
                rede = {}

                def _req(r):
                    if "/api/agent/ask_proxy" in r.url:
                        try:
                            rede["modelo"] = json.loads(r.post_data or "{}").get("ai_chat_model")
                        except Exception:  # noqa: BLE001
                            pass

                def _fim(r):
                    if "/api/agent/ask_proxy" in r.url:
                        rede["fim"] = time.time()
                def _forcar_modelo(route):
                    # conta nova vem com gpt-5.5 de padrão (31/10) e o seletor do DOM não é confiável:
                    # troca o modelo no corpo do pedido
                    try:
                        corpo = json.loads(route.request.post_data or "{}")
                        if corpo.get("ai_chat_model") != MODELO_API:
                            log.info("%s: modelo %s trocado por %s no pedido", apelido, corpo.get("ai_chat_model"),
                                     MODELO_API)
                            rede["trocado"] = True
                            corpo["ai_chat_model"] = MODELO_API
                            route.continue_(post_data=json.dumps(corpo))
                            return
                    except Exception:  # noqa: BLE001
                        pass
                    route.continue_()
                pg.route("**/api/agent/ask_proxy*", _forcar_modelo)  # vale só nesta conexão CDP: registra a cada turno
                pg.on("request", _req)
                pg.on("requestfinished", _fim)
                pg.on("requestfailed", _fim)
                if print_dir:
                    pg.screenshot(path=f"{print_dir}/gs_{apelido}_1.png")
                rede["n_antes"] = _estado(pg).get("n", 0) if conversa else 0
                _enviar(pg, prompt)
                try:
                    resp = _coletar(pg, rede=rede)
                    ULTIMA.info = {"conta": apelido, "url": _url(pg)}
                    if rede.get("modelo") and rede["modelo"] != MODELO_API and not rede.get("trocado"):
                        log.warning("%s respondeu com o modelo %s (esperado %s)", apelido, rede["modelo"], MODELO_API)
                except NaoLogado:
                    marcar_logado(apelido, False, "modal de login ao enviar")
                    raise
                if print_dir:
                    pg.screenshot(path=f"{print_dir}/gs_{apelido}_2.png")
                return resp
        except Exception:
            if br is not None:
                try:
                    br.close()
                except Exception:  # noqa: BLE001
                    pass
                br = None
            _fechar_quente(apelido)  # erro: o próximo pedido abre um Chrome limpo
            raise
        finally:
            if br is not None:
                try:
                    br.close()  # só desconecta o CDP; o Chrome fica quente
                except Exception:  # noqa: BLE001
                    pass
            if apelido in _QUENTES:
                _QUENTES[apelido]["ultimo"] = time.time()


def _fechar_todos_quentes():
    for a in list(_QUENTES):
        _fechar_quente(a)


import atexit  # noqa: E402
atexit.register(_fechar_todos_quentes)  # o CLI e o front não deixam Chrome órfão ao sair


def perguntar(prompt, conta=None, tentativas=6, visivel=False, print_dir=None, conversa=None):
    """Pergunta ao Claude Opus 5.5 pelo Genspark. Usa a 1ª conta pronta da fila (ou uma conta fixa).
    Conta sem cota (paywall) sai da fila até o dia virar e a próxima responde sem gastar tentativa.
    Devolve o texto, ou None se todas falharem."""
    erros, ignorar, erro_final = 0, set(), None
    ULTIMA.info = None
    while erros < tentativas:
        try:
            apelido = conta or proxima_conta(ignorar)
        except RuntimeError as e:  # fila vazia / todas sem cota / todas ocupadas: contrato manda devolver None
            log.warning("sem conta pronta no Genspark: %s", e)
            return None
        t0 = time.time()
        try:
            resp = _uma(apelido, prompt, visivel=visivel, print_dir=print_dir, conversa=conversa)
            if resp and resp.strip():
                marcar_uso(apelido, sucesso=True, segundos=time.time() - t0)
                log.info("OK %s %.1fs %d chars", apelido, time.time() - t0, len(resp))
                return resp
            marcar_uso(apelido, sucesso=False, erro_msg="resposta vazia")
            erro_final = "resposta vazia"
            erros += 1
        except SemCota as e:
            log.warning("%s: %s — próxima conta", apelido, e)
            if isinstance(e, SemOpus):
                marcar_opus(apelido, False)
            else:
                marcar_sem_cota(apelido)
            ignorar.add(apelido)
            erro_final = str(e)
            if conta:
                break
        except NaoLogado as e:
            log.warning("%s: %s", apelido, e)
            ignorar.add(apelido)
            erro_final = str(e)
            if conta:
                break
        except Exception as e:  # noqa: BLE001
            log.error("%s: %s", apelido, str(e)[:150])
            marcar_uso(apelido, sucesso=False, erro_msg=str(e))
            ignorar.add(apelido)
            erro_final = str(e)
            erros += 1
            if conta:
                break
        finally:
            if not conta:
                soltar(apelido)
    log.error("Todas as tentativas falharam: %s", erro_final)
    return None


# ─────────────────────────── CLI ───────────────────────────────────────────
def listar():
    dados = _ler()
    hoje = datetime.now().date().isoformat()
    logadas = com_cota = 0
    for c in sorted(dados["contas"], key=lambda x: x["apelido"]):
        cred = CREDITOS_DIA if c.get("data_cota") != hoje else c.get("creditos", CREDITOS_DIA)
        lg = c.get("logado")
        lg_s = "sim" if lg else ("NÃO" if lg is False else "?")
        st = c.get("stats", {})
        if lg:
            logadas += 1
        if lg and cred >= CUSTO_MSG:
            com_cota += 1
        print(f"  {c['apelido']:32} login={lg_s:3} créd~{cred:3}  "
              f"ok={st.get('ok',0)} err={st.get('erros',0)} {'BLOQ' if c.get('bloqueada') else ''}")
    print(f"\nTotal {len(dados['contas'])} · logadas {logadas} · com cota agora {com_cota} · "
          f"capacidade ~{com_cota * (CREDITOS_DIA // CUSTO_MSG)} msg/dia")


def main():
    import argparse
    p = argparse.ArgumentParser(description="Pool do Genspark (Claude Opus 5.5 grátis)")
    p.add_argument("cmd_ou_pergunta", nargs="?", help="pergunta, ou um comando: semear/login/checar/listar")
    p.add_argument("resto", nargs="*")
    p.add_argument("--conta", help="apelido/email da conta (fixa)")
    p.add_argument("--todas", action="store_true", help="login: refazer todas (não só as pendentes)")
    p.add_argument("--visivel", action="store_true", help="mostrar o Chrome")
    p.add_argument("--prints", action="store_true", help="salvar screenshots em prints/")
    a = p.parse_args()

    cmd = a.cmd_ou_pergunta
    if cmd == "semear":
        semear()
    elif cmd == "login":
        PRINTS.mkdir(exist_ok=True)
        login(conta=a.conta, todas=a.todas, visivel=a.visivel)
    elif cmd == "checar":
        checar(conta=a.conta)
    elif cmd == "listar":
        listar()
    elif cmd:
        pergunta = " ".join([cmd, *a.resto])
        print_dir = str(PRINTS) if a.prints else None
        if a.prints:
            PRINTS.mkdir(exist_ok=True)
        t0 = time.time()
        r = perguntar(pergunta, conta=a.conta, visivel=a.visivel, print_dir=print_dir)
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
