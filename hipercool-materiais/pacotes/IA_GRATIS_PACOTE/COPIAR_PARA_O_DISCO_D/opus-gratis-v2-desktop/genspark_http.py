# -*- coding: utf-8 -*-
r"""genspark_http.py — servidor HTTP compatível com a API da OpenAI, servido pelo pool do Genspark.

Expõe /v1/chat/completions (e /v1/models, /cota) e, por baixo, usa genspark.perguntar: escolhe a 1ª
conta pronta da fila, dirige o Chrome do cofre no chat do Genspark (Claude Opus 5.5) e devolve a
resposta no formato da OpenAI. É o mesmo papel que o gemini_http.py cumpre para o Argon — assim
qualquer cliente OpenAI (incl. o OmniRoute, o Cline, scripts) pode falar com o Opus 5.5 de graça.

Sem dependências externas (http.server). Como cada conta abre um Chrome, a concorrência é limitada
por um semáforo (GENSPARK_VAGAS, padrão 2) para não estourar a RAM da máquina.

    python genspark_http.py                 # sobe em 127.0.0.1:20165
    GENSPARK_PORTA=20165 GENSPARK_VAGAS=2 python genspark_http.py

    curl 127.0.0.1:20165/v1/chat/completions -H "Content-Type: application/json" \
         -d '{"model":"1min/claude-opus-5-5","messages":[{"role":"user","content":"oi"}]}'
"""
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.append(r"D:\hipercool-materiais\comum")
try:
    import sem_janela  # noqa: E402,F401 — roda escondido (pythonw): o node do Playwright não abre janela
except Exception:  # noqa: BLE001  (fora do pc1 a pasta pode não existir — segue sem esconder janela)
    pass
_AQUI = os.path.dirname(os.path.abspath(__file__))  # a própria pasta (portável: desktop, v2)
sys.path.insert(0, _AQUI)
sys.path.insert(0, os.path.join(_AQUI, "umin"))
import genspark  # noqa: E402
try:
    import genspark_http_puro as gpuro  # Genspark por HTTP puro (ZERO navegador) — modo principal (desktop 31/10)
except Exception:  # noqa: BLE001
    gpuro = None
try:
    import genspark_pagina as gpagina  # Genspark por página quente (navegador hospedeiro) — backup
except Exception:  # noqa: BLE001
    gpagina = None
try:
    import umin  # 1min.ai pela API (Opus 5.5 / Fable 5.1 etc.) — do "outro chat", não mexo nele
except Exception:  # noqa: BLE001
    umin = None

PORTA = int(os.environ.get("GENSPARK_PORTA", "20165"))   # 20160 é do cline-ponte; 20165 livre
VAGAS = int(os.environ.get("GENSPARK_VAGAS", "2"))       # Chromes simultâneos do Genspark (RAM!)

# Cada modelo exposto é uma LISTA de tentativas (backend, modelo-no-backend), em ordem de preferência.
# backend "genspark" = pool de navegador (62 contas, grátis/dia); "1min" = API do 1min.ai (rápida, confiável).
# - os ids com prefixo usam SÓ aquele backend;
# - os ids "auto" (sem prefixo) tentam o Genspark primeiro (cota grátis do dia) e caem no 1min se faltar — "quem tiver crédito".
# Sonnet/Haiku do 1min NÃO são servidos (decisão da dona): ficam documentados como disponíveis (veja PROGRESSO/_DOC).
# backends do Genspark Opus 5.5 (grátis): puro = HTTP puro SEM navegador (~5 s, melhor); pagina = fetch de dentro da
# página quente (navegador hospedeiro, backup); genspark = automação de tela antiga (com reuso de conversa, ~45-60 s).
AUTO_OPUS = os.environ.get("GENSPARK_AUTO", "puro,pagina,1min")  # ordem do "auto": PURO → PÁGINA → 1min (reserva)
def _backend(b):
    b = b.strip()
    return ("1min", "opus") if b == "1min" else (b, None)  # puro | pagina | genspark
_ordem = [_backend(b) for b in AUTO_OPUS.split(",")]

MODELOS = {
    # auto: usa quem tiver crédito (PURO sem navegador primeiro, PÁGINA de backup, 1min de reserva)
    "claude-opus-5-5": _ordem,
    # Genspark, escolhendo o backend:
    "puro/claude-opus-5-5": [("puro", None)],          # HTTP puro, sem navegador
    "pagina/claude-opus-5-5": [("pagina", None)],      # página quente (navegador)
    # CORREÇÃO OBRIGATÓRIA (pc1, 31/10 — ver CLAUDE.md): é o id que a VPS manda (PONTES do proxy 20133,
    # "genspark-opus-5-5"). Só-tela aqui = 15-100 s e tool-call errado no Claude Code. Sem navegador primeiro.
    "genspark/claude-opus-5-5": [("puro", None), ("pagina", None), ("genspark", None)],
    "tela/claude-opus-5-5": [("genspark", None)],  # automação de tela (antigo, com reuso de conversa)
    # mesmos backends com prefixo genspark/ — é o único que o proxy_cc (:20166) manda à ponte; são os do seletor do VS Code
    "genspark/claude-opus-5-5-puro": [("puro", None), ("pagina", None), ("1min", "opus")],
    "genspark/claude-opus-5-5-pagina": [("pagina", None), ("puro", None), ("1min", "opus")],
    # PURO com token do serviço de captcha pago (CapSolver/2captcha; chave em segredos/captcha.key). Sem reserva de
    # propósito: é para testar/usar o serviço — sem chave, o erro diz o que falta.
    "genspark/claude-opus-5-5-captcha": [("puro_captcha", None)],
    # 1min pela API:
    "1min/claude-opus-5-5": [("1min", "opus")],
    "1min/claude-opus-5": [("1min", "opus5")],
    # Fable: modelo separado (só 1min)
    "claude-fable-5-1": [("1min", "fable")],
    "1min/claude-fable-5-1": [("1min", "fable")],
}
# Disponíveis no 1min mas NÃO acionados (a dona pediu só documentar): sonnet -> us.anthropic.claude-sonnet-5-5,
# haiku -> us.anthropic.claude-haiku-5-5. Para ligar, bastaria acrescentar ao MODELOS.
MODELO_PADRAO_ID = "claude-opus-5-5"  # modelo desconhecido cai no auto (Opus 5.5)

_sem = threading.Semaphore(VAGAS)


# ─────────── reuso de conversa (copiado do gemini_http_proxy do Argon) ───────────
# Depois de cada resposta do Genspark guardo {conta, url da conversa} pela chave = hash das mensagens enviadas. No turno
# seguinte o Claude Code reenvia essas mensagens + a resposta (assistant) + o que é novo: se o começo bate, mando SÓ o
# que veio depois do assistant, na mesma conversa da mesma conta. Qualquer falha = histórico inteiro como antes.
import hashlib  # noqa: E402

CONVERSAS = {}
_trava_conv = threading.Lock()
CONV_TTL = 60 * 60
CONV_MAX = 400
REUSO = {"acertos": 0, "falhas": 0, "chars_poupados": 0}


def _chave(msgs):
    norm = []
    for m in msgs:
        c = m.get("content") or ""
        if isinstance(c, list):
            c = " ".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
        norm.append([m.get("role", "user"), " ".join(str(c).split())])
    return hashlib.sha1(json.dumps(norm, ensure_ascii=False).encode("utf-8")).hexdigest()


def _achar_continuacao(msgs):
    """(sessão, índice do assistant) se o histórico continua uma conversa conhecida; senão None."""
    if len(msgs) < 3:
        return None
    with _trava_conv:
        for i in range(len(msgs) - 1, 0, -1):
            if msgs[i].get("role") != "assistant":
                continue
            s = CONVERSAS.get(_chave(msgs[:i]))
            if s and time.time() - s["t"] < CONV_TTL:
                return s, i
    return None


def _guardar(msgs, info):
    if not info:
        return
    with _trava_conv:
        if len(CONVERSAS) >= CONV_MAX:
            for k in sorted(CONVERSAS, key=lambda k: CONVERSAS[k]["t"])[:CONV_MAX // 4]:
                CONVERSAS.pop(k, None)
        CONVERSAS[_chave(msgs)] = {**info, "t": time.time()}


def _prompt_continuacao(msgs, i):
    novas = [m for m in msgs[i + 1:] if m.get("role") != "system"]
    return ("[Continuação desta mesma conversa: o agente executou o que você pediu e o resultado e as mensagens novas "
            "vêm abaixo; as instruções do início continuam valendo. Continue como Assistente; não repita uma "
            "ferramenta que já devolveu resultado.]\n\n" + _flatten(novas, fecho=False))


def _genspark(msgs, prompt, conta):
    """Genspark com reuso de conversa; devolve o texto (ou None)."""
    cont = None if conta else _achar_continuacao(msgs)
    if cont:
        s, i = cont
        curto = _prompt_continuacao(msgs, i)
        texto = genspark.perguntar(curto, conta=s["conta"], conversa=s["url"], tentativas=1)
        if texto and texto.strip():
            REUSO["acertos"] += 1
            REUSO["chars_poupados"] += max(0, len(prompt) - len(curto))
            _guardar(msgs, getattr(genspark.ULTIMA, "info", None))
            return texto
        REUSO["falhas"] += 1  # conta sem cota/conversa sumiu: segue com o histórico inteiro
    texto = genspark.perguntar(prompt, conta=conta)
    if texto and texto.strip():
        _guardar(msgs, getattr(genspark.ULTIMA, "info", None))
    return texto


TETO_1MIN = int(os.environ.get("GENSPARK_TETO_1MIN", "15000"))  # créditos por consulta ao 1min (nunca mais que isso)


def _rotear(model, prompt, conta, msgs=()):
    """Roteia pelo nome do modelo. Devolve (texto, id_exposto). Tenta cada backend da lista em ordem; o 1º que
    responder (texto não-vazio) ganha — é o "quem tiver crédito". 1min = API (sem semáforo); genspark = navegador
    (sob o semáforo de RAM, 1 por vez)."""
    mid = model if model in MODELOS else MODELO_PADRAO_ID
    ultimo = None
    for backend, bmod in MODELOS[mid]:
        try:
            if backend == "1min":
                if umin is None:
                    ultimo = "umin (1min) indisponível"
                    continue
                reservas = ("opus5",) if bmod == "opus" else ()  # Opus 5.5 na AWS às vezes dá 503: cai pro Opus 5
                p1 = prompt
                if msgs:
                    # 31/10 17h30 (dona: "deixa ele responder todas que der até acabar as contas"): o 1min recusa
                    # quando a ESTIMATIVA (~3,9 créditos/char) passa do saldo, e cobra o real (~5,4/char) mesmo
                    # deixando negativo. Corta o prompt para caber no saldo da conta com mais crédito; cada turno
                    # gasta ~a conta inteira. Sem conta que caiba 15 mil chars -> "sem cota" (a VPS pula o 1min).
                    melhor = umin._proxima()
                    # 31/10 18h (dona): "consultas até 15 mil e nunca mais do que isso". Custo real ≈ 5,4 créditos/char
                    # (entrada+saída); reserva 700 chars para a resposta (o cérebro pede ≤ 600).
                    caber = int(min(umin._saldo(melhor), TETO_1MIN) / 5.4) - 700 if melhor else 0
                    if caber < 1500:  # 31/10: métrica "15 mil = 1 msg curta" (~3,5 mil chars cabem); abaixo disso não
                        raise RuntimeError("1min: sem cota (nenhuma conta aguenta nem uma mensagem curta)")
                    p1 = _flatten(list(msgs), limite=min(caber, LIMITE_PROMPT))
                    # 31/10 18h40: no 1min a SAÍDA custa ~9x a entrada e o raciocínio é cobrado como saída (263 chars de
                    # entrada + 1.276 de saída = 59 mil créditos). Sem o pedido de "raciocínio máximo" aqui.
                    p1 = p1.replace(PEDIDO_RACIOCINIO, "").strip()
                texto, _info = umin.perguntar(p1, modelo=bmod, reservas=reservas)
            elif backend == "puro":
                if gpuro is None:
                    ultimo = "genspark puro indisponível"
                    continue
                texto = gpuro.perguntar(prompt, conta=conta)  # HTTP puro, sem navegador (sem semáforo)
            elif backend == "puro_captcha":
                if gpuro is None:
                    ultimo = "genspark puro indisponível"
                    continue
                texto = gpuro.perguntar(prompt, conta=conta, token_modo="<SEGREDO_REMOVIDO>")  # HTTP puro + token do serviço pago
            elif backend == "pagina":
                if gpagina is None:
                    ultimo = "genspark página indisponível"
                    continue
                texto = gpagina.perguntar_quente(prompt, conta=conta)  # página quente gerencia a própria RAM
            else:  # "genspark": automação de tela antiga, com reuso de conversa
                with _sem:  # 1 navegador por vez (RAM)
                    texto = _genspark(list(msgs), prompt, conta)
            if texto and texto.strip():
                return texto, mid
            ultimo = f"{backend}: resposta vazia/sem cota"
        except Exception as e:  # noqa: BLE001  tenta o próximo backend
            ultimo = f"{backend}: {e}"
    if ultimo:
        raise RuntimeError(ultimo)
    return None, mid


def _flatten(mensagens, fecho=True, limite=None):
    """Junta as mensagens num único prompt com rótulos de papel (ponte simples de chat web).
    31/10: no chat do Genspark tudo vira UMA mensagem do usuário; com o rótulo "Instruções:" o Opus tratava as regras
    do Claude Code (protocolo ```tool_call) como texto colado e respondia "não tenho acesso à ferramenta". Medido:
    apresentado como o agente ao qual ele está conectado, ele chama a ferramenta certo."""
    cabeca, conversa = [], []
    if any(m.get("role") == "system" for m in mensagens):
        cabeca.append("Você está conectado a um agente de código (como o Claude Code), que lê esta conversa e executa "
                      "de verdade as ferramentas que você pedir no formato descrito abaixo. Siga as instruções do agente.")
    tem_ferramentas = bool(_nomes_ferramentas(mensagens))
    for m in mensagens:
        papel = {"system": "Instruções do agente", "user": "Usuário", "assistant": "Assistente"}.get(m.get("role"), m.get("role", ""))
        cont = m.get("content") or ""   # content pode vir null (ex.: mensagem de tool-call) -> "" em vez do literal "None"
        if isinstance(cont, list):  # formato OpenAI com blocos
            cont = " ".join(b.get("text", "") for b in cont if isinstance(b, dict) and b.get("type") == "text")
        if tem_ferramentas and m.get("role") == "assistant" and _fala_sem_ferramenta(cont):
            # 31/10 09h44 (pc1): a mesma sessão abriu o navegador e na mensagem seguinte disse "não tenho terminal" —
            # ele segue as próprias falas antigas de "não há ferramenta". Elas saem do histórico (eram falsas).
            cont = ("[resposta anterior omitida: ela dizia, POR ENGANO, que não havia ferramenta de terminal/execução "
                    "nesta sessão. Isso estava errado — as ferramentas listadas funcionam e devem ser usadas.]")
        (cabeca if m.get("role") == "system" else conversa).append(f"{papel}: {cont}".strip())
    # 31/10: a conversa chega inteira numa mensagem só; sem este fecho, no 2º turno ele pedia a MESMA ferramenta de
    # novo em vez de usar o resultado que já veio (tratava a transcrição como exemplo, não como o que já aconteceu)
    fim = []
    if fecho and len(conversa) > 1:
        fim.append("(A conversa acima já aconteceu de verdade, inclusive os resultados das ferramentas. Agora é a "
                   "sua vez, como Assistente: continue a partir da última mensagem. Não repita uma ferramenta que "
                   "já devolveu resultado; use o resultado.)")
    # 31/10 10h40 (pc1, dona: "thinking no máximo como o Argon e o Sonnet web"): o Genspark ignora campos de thinking
    # no corpo (enable_thinking/thinking/reasoning_effort: 65-70 tokens iguais) e "claude-opus-5-5-thinking" vira
    # Sonnet 4.5 em silêncio. O que funciona é pedir no texto: reasoning_tokens 0 -> 128-168 no mesmo Opus 5.5.
    fim.append(PEDIDO_RACIOCINIO)
    nomes = _nomes_ferramentas(mensagens)
    if nomes:
        # 31/10 11h50 (pc1, dona): com raciocínio baixo ele PARA — anuncia o que "vai fazer", lança Workflow/subagente e
        # fica esperando, ou recusa tarefa nova dizendo que "um workflow está em execução". Ordem forte no fim do prompt.
        fim.append(PEDIDO_EXECUTAR)
        # 31/10 pc1: numa conversa em que ele inventou "Run" (não existe; o proxy ignorou), ele concluiu "não há terminal
        # nesta sessão" e passou a pedir para a dona rodar. O lembrete no FIM (onde pesa mais) desfaz isso.
        shell = [n for n in ("PowerShell", "Bash") if n in nomes]
        fim.append("(Ferramentas que existem nesta sessão — use o nome EXATO no bloco ```tool_call: " + ", ".join(nomes)
                   + "." + (f" Para rodar comando no computador use {' ou '.join(shell)}; você PODE rodar, não peça "
                            "ao usuário para rodar." if shell else "")
                   + " Se antes alguma chamada não executou, foi por nome errado: chame de novo com o nome certo.)")
    return _caber(cabeca, conversa, fim, limite)


PEDIDO_RACIOCINIO = ("(Raciocínio: use o MÁXIMO de raciocínio/pensamento estendido antes de responder — pense passo a "
                     "passo, confira cada etapa e procure erros no próprio raciocínio. Só então responda.)")

PEDIDO_EXECUTAR = (
    "(MODO DE TRABALHO — leia com atenção:\n"
    "1. FAÇA a tarefa você mesmo, agora, chamando as ferramentas (```tool_call) até ela estar REALMENTE pronta, "
    "conferida e testada. Só responda em texto puro, sem bloco de ferramenta, quando tudo estiver feito e verificado "
    "— porque a resposta só em texto ENCERRA o seu turno.\n"
    "2. NÃO pare para anunciar o que 'vai fazer': em vez de escrever 'vou ler/editar/rodar/verificar', já escreva o "
    "bloco ```tool_call que faz isso, na MESMA resposta. Nada de 'aguarde', 'na próxima etapa', 'quando a execução "
    "voltar'.\n"
    "3. NÃO delegue para fugir do trabalho: não lance Workflow, Agent, subagente nem tarefa em segundo plano e fique "
    "esperando o resultado. Você tem as ferramentas de leitura, edição e terminal — faça direto com elas. Só use um "
    "subagente se o pedido pedir isso em palavras; mesmo assim, continue trabalhando, não pare para esperar.\n"
    "4. Cada nova mensagem do Usuário é uma ordem para AGIR AGORA. Nunca recuse uma tarefa nova dizendo que 'um "
    "workflow/uma execução está em andamento' ou que 'não pode agora': atenda o novo pedido de imediato com as "
    "ferramentas.\n"
    "5. Se forem vários itens/pendências, resolva TODOS, um por um, e só dê a resposta final quando cada um estiver "
    "feito e validado. Não entregue lista de 'o que falta' como se fosse o fim.)")

_NOMES_SHELL_FALSOS = ("Run", "Shell", "Terminal", "Execute", "Exec", "Cmd", "RunCommand", "run_command", "shell",
                       "bash", "powershell", "terminal", "run")


def _nomes_ferramentas(mensagens):
    """Nomes das ferramentas que o proxy da VPS listou no system ("Ferramentas disponiveis:\\n- Nome: ...")."""
    txt = "\n".join(str(m.get("content") or "") for m in mensagens if m.get("role") == "system")
    i = txt.find("Ferramentas disponiveis:")
    if i < 0:
        return []
    return _re.findall(r"^- ([A-Za-z_][\w-]*): ", txt[i:], _re.M)


def _corrigir_nomes(resp, nomes):
    """Troca nome de shell inventado ("Run", "Terminal"...) pela ferramenta de terminal real da sessão."""
    shell = next((n for n in ("PowerShell", "Bash") if n in nomes), None)
    if not shell or "```tool_call" not in resp:
        return resp
    for falso in _NOMES_SHELL_FALSOS:
        if falso in nomes:
            continue
        resp = _re.sub(r'("name"\s*:\s*")' + _re.escape(falso) + r'"', r"\g<1>" + shell + '"', resp)
    return resp


# 31/10 (medido): o Genspark CORTA a mensagem em 200.000 caracteres e fica com o COMEÇO — numa conversa longa do Claude
# Code (161 turnos) a pergunta nova, que fica no fim, sumia e o Opus respondia "não há nova solicitação". Aqui o prompt
# é montado para caber: instruções (com teto) + as mensagens MAIS RECENTES; as antigas viram um aviso de omissão.
LIMITE_PROMPT = int(os.environ.get("GENSPARK_LIMITE_PROMPT", "185000"))  # folga abaixo dos 200.000 do Genspark
TETO_INSTRUCOES = int(os.environ.get("GENSPARK_TETO_INSTRUCOES", "60000"))


# 31/10 09h40 (desktop): com só "as mais recentes", uma sessão de 517 mil chars mandava 16-26 de 199 mensagens (cada
# resultado de ferramenta tem até 30 mil chars) — o Opus perdia o pedido original e o assunto, "misturava" e parava.
# Agora: (1) as INTEIRAS_RECENTES últimas mensagens vão inteiras; (2) nas anteriores, cada resultado de ferramenta
# encolhe para começo+fim e textos muito longos idem; (3) o 1º pedido do usuário (o objetivo da sessão) fica fixo no topo.
INTEIRAS_RECENTES = int(os.environ.get("GENSPARK_INTEIRAS_RECENTES", "8"))
RESULTADO_ANTIGO = 1400   # chars que sobram de cada resultado de ferramenta antigo (900 do começo + 500 do fim)
TEXTO_ANTIGO = 5000       # teto de qualquer mensagem antiga
PEDIDO_FIXO = 6000        # teto do 1º pedido do usuário fixado no topo


def _encolher_antiga(parte):
    import re as _r

    def _resultado(m):
        corpo = m.group(2)
        if len(corpo) <= RESULTADO_ANTIGO:
            return m.group(0)
        return (m.group(1) + corpo[:900] + f"\n[... {len(corpo) - 1400} chars deste resultado antigo omitidos ...]\n"
                + corpo[-500:] + m.group(3))

    parte = _r.sub(r"(\[resultado da ferramenta[^\]]*\]\n)(.*?)(\n\[fim do resultado\])", _resultado, parte, flags=_r.S)
    if len(parte) > TEXTO_ANTIGO:
        parte = parte[:3500] + f"\n[... {len(parte) - 4700} chars desta mensagem antiga omitidos ...]\n" + parte[-1200:]
    return parte


def _caber(cabeca, conversa, fim, limite=None):
    limite = limite or LIMITE_PROMPT
    sep = "\n\n"
    total = len(sep.join(cabeca + conversa + fim))
    if total <= limite:
        return sep.join(cabeca + conversa + fim)
    cab = sep.join(cabeca)
    teto = min(TETO_INSTRUCOES, int(limite * 0.6))  # limite pequeno (1min): as instruções não podem comer tudo
    if len(cab) > teto:  # instruções gigantes: fica o começo (regras/ferramentas) e avisa
        cab = cab[:teto] + "\n[... instruções do agente cortadas aqui por tamanho ...]"
    cauda = sep.join(fim)
    # 1º pedido do usuário = objetivo da sessão: fica fixo (encolhido se for enorme). Os <system-reminder> do Claude Code
    # (memória, instruções) vêm no começo dessa mensagem e ocupariam todo o teto: saem do pedido fixo.
    import re as _r
    i_pedido, p0 = None, ""
    for i, p in enumerate(conversa):
        if not p.startswith("Usuário:"):
            continue
        limpo = _r.sub(r"<system-reminder>.*?</system-reminder>", "", p, flags=_r.S)
        limpo = _r.sub(r"\[resultado da ferramenta[^\]]*\]\n.*?\n\[fim do resultado\]", "", limpo, flags=_r.S).strip()
        if len(limpo) > len("Usuário:") + 3:
            i_pedido, p0 = i, limpo
            break
    fixo = ""
    if i_pedido is not None and i_pedido < len(conversa) - INTEIRAS_RECENTES:
        fixo = "[Pedido que abriu esta conversa — o objetivo geral da sessão]\n" + (
            p0 if len(p0) <= PEDIDO_FIXO else p0[:PEDIDO_FIXO] + "\n[... resto deste pedido omitido ...]")
    sobra = limite - len(cab) - len(cauda) - len(fixo) - 600
    mantidas = []
    for n, parte in enumerate(reversed(conversa)):  # da mais nova para a mais antiga
        idx = len(conversa) - 1 - n
        if idx == i_pedido and fixo:
            continue  # já vai fixo no topo
        if n >= INTEIRAS_RECENTES:
            parte = _encolher_antiga(parte)
        if len(parte) + len(sep) > sobra:
            if not mantidas:  # nem a última mensagem cabe inteira: fica o FIM dela (onde está o pedido)
                mantidas.append("[... começo desta mensagem cortado por tamanho ...]\n" + parte[-max(sobra - 80, 1000):])
            break
        mantidas.append(parte)
        sobra -= len(parte) + len(sep)
    omitidas = len(conversa) - len(mantidas) - (1 if fixo else 0)
    aviso = (f"[{omitidas} mensagens antigas desta conversa foram omitidas e os resultados de ferramenta mais antigos "
             "foram encurtados, porque o chat tem limite de tamanho. O pedido atual é a última mensagem do Usuário; "
             "continue o trabalho da sessão a partir dele.]") if omitidas > 0 else (
             "[Os resultados de ferramenta mais antigos foram encurtados porque o chat tem limite de tamanho.]")
    print(f"prompt {total} chars > {limite}: mantive {len(mantidas)} de {len(conversa)} mensagens"
          f" (antigas encolhidas{', 1º pedido fixo' if fixo else ''})", flush=True)
    return sep.join([p for p in [cab, fixo, aviso] if p] + list(reversed(mantidas)) + ([cauda] if cauda else []))


import re as _re  # noqa: E402

# CORREÇÃO OBRIGATÓRIA (pc1, 31/10): às vezes o Opus do Genspark responde "não tenho acesso à ferramenta" mesmo com o
# protocolo ```tool_call no prompt (1 em ~5 pela VPS). O front repete 1x com este lembrete no FIM.
# 10h50 (pc1, achado pelo genspark-ajudante e corrigido pelo Opus principal): "_NAO_MENTAL" = não vale quando a frase
# é sobre executar "mentalmente"/um exemplo conceitual; "_DISP" = "não há/tenho ... ferramenta" só vale se a frase
# nega disponibilidade/acesso ("não há uma ferramenta especial neste exemplo" não é recusa).
_NAO_MENTAL = r"(?![^.\n]{0,50}\b(mentalmente|de cabe[çc]a|conceitual|te[óo]ric))"
_DISP = (r"(?=[^.\n]{0,50}\b(dispon[íi]ve|indispon[íi]ve|acesso|acess[íi]ve|existe|presente|nest[ae] (sess|conversa|"
         r"chat|ambiente)|aqui\b|agora\b|local|para (executar|rodar|abrir)))")
_RECUSA = _re.compile(r"n[ãa]o (tenho|possuo) acesso|n[ãa]o (consigo|posso) (executar|rodar|acessar)" + _NAO_MENTAL + "|"
                      r"don'?t have access|can'?t (execute|run)|unable to (execute|run)|sem acesso [àa]s? ferramenta|"
                      r"n[ãa]o h[áa] (uma )?ferramenta" + _DISP + r"|execute no (powershell|terminal)|cole aqui a sa[íi]da|"
                      r"n[ãa]o [ée] uma ferramenta dispon|"
                      # 09:05: "não tenho uma ferramenta local de PowerShell/Bash disponível", "não tenho a ferramenta
                      # de execução do computador disponível", "se você reabrir a sessão com as ferramentas locais"
                      r"n[ãa]o (tenho|h[áa]|disponho de|possuo)\b[^.\n]{0,60}\b(ferramenta|terminal|powershell|bash)"
                      + _DISP + "|"
                      r"reabrir a sess[ãa]o|ferramentas locais|sem (o )?(terminal|powershell|bash)|"
                      # 09:42/09:44 (pc1): "a ferramenta de execução local/PowerShell não está disponível aqui", "não
                      # consigo abrir o navegador nesta sessão", "esse agente não está conectado às ferramentas",
                      # "quando a execução local voltar" — escapavam; pega a forma geral (negação perto de ferramenta)
                      r"(ferramenta|terminal|powershell|bash|execu[çc][ãa]o)[^.\n]{0,80}\b(n[ãa]o (est[áa]|fica|existe)|"
                      r"indispon[íi]ve(l|is))|n[ãa]o (consigo|posso|tenho como)\b[^.\n]{0,40}\b(abrir|executar|rodar|"
                      r"acessar|usar)\b" + _NAO_MENTAL + r"|n[ãa]o est[áa] conectad[oa][^.\n]{0,60}ferramenta|"
                      r"quando (a )?(execu[çc][ãa]o|ferramenta)[^.\n]{0,40}(voltar|estiver dispon)|"
                      r"not available in this session|no (shell|terminal) (tool|access)|"
                      # 10h50: 4 formas achadas pelo ajudante ("este ambiente não permite executar comandos", "não
                      # tenho um meio local para executar", "você precisa rodar no seu PowerShell e me enviar a saída",
                      # "a execução precisa ser feita fora deste chat")
                      r"ambiente[^.\n]{0,60}\bn[ãa]o\b[^.\n]{0,40}\b(permite|dispon[íi]vel|executar|rodar)\b|"
                      r"n[ãa]o (tenho|h[áa]|possuo)\b[^.\n]{0,40}\b(meio|forma|jeito)\b[^.\n]{0,40}\b(executar|rodar|comando)|"
                      r"(precisa|deve|tem que)\b[^.\n]{0,100}\b(rodar|executar)\b[^.\n]{0,100}\b(seu |sua )?(computador|"
                      r"terminal|powershell|bash|m[áa]quina)\b[^.\n]{0,80}\b(sa[íi]da|resultado|retorno)\b|"
                      r"execu[çc][ãa]o[^.\n]{0,60}\bfora (deste|do|da) (chat|conversa)", _re.I)


_CERCA_SOBRA = _re.compile(r"^[ \t]*`{2,}[ \t]*(tool_call|json)?[ \t]*$", _re.M)


def _normalizar_chamadas(resp, nomes):
    """31/10 10h37 (pc1): o Opus escreveu a chamada como JSON solto com a cerca errada ("``" no fim, sem ```tool_call)
    e o proxy da VPS — que só reconhece ```tool_call/```json bem fechados — mostrou como texto: nada executou.
    Acha TODO objeto {"name": <ferramenta da sessão>, "input": {...}} válido (com cerca certa, errada ou sem cerca) e
    reescreve cada um como ```tool_call bem fechado. Devolve (resposta, quebrada): quebrada = havia chamada que não deu
    para ler (JSON cortado/ inválido) e nenhuma válida — o do_POST pede de novo."""
    if not nomes or not resp or '"name"' not in resp:
        return resp, False
    shell = next((n for n in ("PowerShell", "Bash") if n in nomes), None)
    validos = set(nomes) | ({f for f in _NOMES_SHELL_FALSOS if f not in nomes} if shell else set())
    dec = json.JSONDecoder()
    chamadas, partes, fim = [], [], 0
    for m in _re.finditer(r'\{\s*"name"\s*:\s*"([^"]+)"', resp):
        if m.start() < fim or m.group(1) not in validos:
            continue
        try:
            obj, f = dec.raw_decode(resp, m.start())
        except ValueError:
            continue
        if not isinstance(obj, dict) or not isinstance(obj.get("input"), dict):
            continue
        partes.append(resp[fim:m.start()])
        nome = obj["name"] if obj["name"] in nomes else shell  # "Run"/"Terminal"... -> terminal real
        chamadas.append({"name": nome, "input": obj["input"]})
        fim = f
    if not chamadas:
        quebrada = any(m.group(1) in validos for m in _re.finditer(r'\{\s*"name"\s*:\s*"([^"]+)"', resp))
        return resp, quebrada
    partes.append(resp[fim:])
    texto = _CERCA_SOBRA.sub("", "".join(partes)).strip()
    blocos = "\n".join("```tool_call\n" + json.dumps(c, ensure_ascii=False) + "\n```" for c in chamadas)
    return (texto + "\n\n" + blocos) if texto else blocos, False


def _fala_sem_ferramenta(texto):
    """Resposta do assistente que diz (por engano) não ter terminal/ferramenta e não chamou nenhuma."""
    return "```tool_call" not in texto and bool(
        _RECUSA.search(texto) or (_BLOCO_SHELL.search(texto) and _PEDE_RODAR.search(texto)))
_BLOCO_SHELL = _re.compile(r"```(powershell|ps1|pwsh|bash|sh|shell|cmd|bat|console)\s*\n", _re.I)
# o bloco de shell só conta como "mandou a dona rodar" se vier com pedido para ELA executar (senão pode ser um comando
# que ela pediu só para ver — repetir forçaria a execução)
_PEDE_RODAR = _re.compile(r"\b(execute|rode|roda|executa|cole|colar|me (mande|envie|passe) a sa[íi]da|envie a sa[íi]da|"
                          r"run (this|it)|paste|no seu (terminal|powershell)|no powershell:|no terminal:)\b", _re.I)
LEMBRETE_FERRAMENTA = (
    "\n\n(Lembrete do agente: você TEM acesso às ferramentas listadas acima. Usar uma ferramenta = escrever o bloco "
    "```tool_call com o JSON {\"name\", \"input\"}; o agente lê o seu texto e executa de verdade no computador do "
    "usuário. Responda agora com o(s) bloco(s) ```tool_call necessário(s), sem dizer que não tem acesso.)")


def _tokens(txt):
    return max(1, len(txt or "") // 4)


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):  # silencia o log padrão (ruidoso)
        pass

    def _json(self, code, obj):
        corpo = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        if self.path.rstrip("/") == "/v1/models":
            self._json(200, {"object": "list", "data": [
                {"id": mid, "object": "model", "owned_by": backends[0][0]}
                for mid, backends in MODELOS.items()]})
        elif self.path.rstrip("/") in ("/cota", "/health", ""):
            import monitor_genspark
            r = monitor_genspark.resumo()
            if isinstance(r, dict):
                r = {**r, "reuso": REUSO}
            self._json(200, r)
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        if self.path.rstrip("/") != "/v1/chat/completions":
            self._json(404, {"error": "not found"})
            return
        try:
            n = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(n) or b"{}")
        except Exception as e:  # noqa: BLE001
            self._json(400, {"error": {"message": f"corpo inválido: {e}"}})
            return
        prompt = _flatten(req.get("messages", []))
        try:  # último pedido cru (diagnóstico do protocolo de ferramentas; _teste_ferramenta.py reenvia pelo PURO)
            with open(os.path.join(_AQUI, "ultimo_pedido.json"), "w", encoding="utf-8") as f:
                json.dump(req, f, ensure_ascii=False, indent=1)
        except OSError:
            pass
        stream = bool(req.get("stream"))
        conta = req.get("conta") or self.headers.get("x-genspark-conta")
        model = req.get("model") or MODELO_PADRAO_ID
        t0 = time.time()
        try:
            resp, usado_id = _rotear(model, prompt, conta, req.get("messages", []))
            # recusa, ou "rode você este comando" (bloco ```powershell/```bash sem tool_call) quando há terminal na sessão
            nomes = _nomes_ferramentas(req.get("messages", []))
            tem_shell = bool({"PowerShell", "Bash"} & set(nomes))
            for tentativa in range(2):  # até 2 repetições (conversa "convencida" pelo histórico de que não há terminal)
                resp, quebrada = _normalizar_chamadas(resp, nomes)  # cerca errada/sem cerca -> ```tool_call certo
                if not (resp and "```tool_call" in prompt and (quebrada or ("```tool_call" not in resp and (
                        _RECUSA.search(resp) or
                        (_BLOCO_SHELL.search(resp) and _PEDE_RODAR.search(resp) and tem_shell))))):
                    break
                print(f"[{time.strftime('%H:%M:%S')}] recusa de ferramenta; repetindo com lembrete ({tentativa + 1}/2)",
                      flush=True)
                try:  # guarda o caso para achar a causa (diag_ajudante\recusas\; os 30 mais recentes)
                    pasta = os.path.join(_AQUI, "diag_ajudante", "recusas")
                    os.makedirs(pasta, exist_ok=True)
                    with open(os.path.join(pasta, f"recusa_{time.strftime('%H%M%S')}_{tentativa + 1}.json"), "w",
                              encoding="utf-8") as f:
                        json.dump({"resposta": resp, "pedido": req}, f, ensure_ascii=False)
                    for velho in sorted(os.listdir(pasta))[:-30]:
                        os.remove(os.path.join(pasta, velho))
                except OSError:
                    pass
                extra = LEMBRETE_FERRAMENTA + (
                    f"\n(A ferramenta de terminal ESTÁ disponível agora com o nome {' e '.join(n for n in ('PowerShell', 'Bash') if n in nomes)}"
                    ". O que foi dito antes na conversa sobre não haver terminal estava errado: era o nome 'Run', que "
                    "não existe.)" if tem_shell else "")
                resp2, _ = _rotear(model, prompt + extra, conta, [])
                if resp2:
                    resp = resp2
            if resp:
                resp = _corrigir_nomes(resp, nomes)
                resp, quebrada = _normalizar_chamadas(resp, nomes)  # a repetição também pode ter vindo com cerca errada
                if "```tool_call" in prompt and (quebrada or ("```tool_call" not in resp and (
                        _RECUSA.search(resp) or (_BLOCO_SHELL.search(resp) and _PEDE_RODAR.search(resp) and tem_shell)))):
                    # 31/10 10h55 (pc1): recusou mesmo depois das 2 repetições (visto 2x em 1 h). Em vez de entregar a
                    # recusa, devolve 429 com "Nenhuma conta com cota": a VPS põe o MESMO Opus 5.5 (opus-auto) no lugar
                    # deste turno (correção 12) — nunca modelo inferior.
                    print(f"[{time.strftime('%H:%M:%S')}] recusa persistiu após 2 repetições -> Opus Automático na VPS",
                          flush=True)
                    self._json(429, {"error": {"message": "Nenhuma conta com cota: o Genspark recusou usar as "
                                               "ferramentas 3 vezes neste turno (recusa)", "type": "no_quota"}})
                    return
        except Exception as e:  # noqa: BLE001  nunca deixar a exceção escapar do handler (conexão penduraria)
            # 31/10 12h (pc1): todas as contas sem cota -> _rotear levanta "resposta vazia/sem cota". Isso tem que virar
            # 429 (que a VPS reconhece e cai no Opus Automático), não 500 (que a VPS transforma em 502 morto).
            msg = str(e).lower()
            if any(s in msg for s in ("sem cota", "resposta vazia", "nenhuma conta", "insufficient", "sem opus",
                                      "no_quota", "sem cr[eé]dito", "sem crédito", "paywall")):
                self._json(429, {"error": {"message": "Nenhuma conta com cota agora no Genspark", "type": "no_quota"}})
                return
            self._json(500, {"error": {"message": f"erro interno: {e}", "type": "internal"}})
            return
        if not resp:
            # "Nenhuma conta com cota" é o texto que o proxy da VPS (:20133) reconhece: lá o Sonnet web responde no
            # lugar, com aviso na 1ª linha, em vez de um erro seco no Claude Code
            self._json(429, {"error": {"message": "Nenhuma conta com cota agora no Genspark", "type": "no_quota"}})
            return
        cid = f"chatcmpl-{int(t0)}"
        if stream:
            self._stream(cid, resp, usado_id)
        else:
            self._json(200, {
                "id": cid, "object": "chat.completion", "created": int(t0), "model": usado_id,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": resp}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": _tokens(prompt), "completion_tokens": _tokens(resp),
                          "total_tokens": _tokens(prompt) + _tokens(resp)},
            })

    def _stream(self, cid, resp, model_id):
        # sem Content-Length no SSE: fecho a conexão pra DELIMITAR o corpo (HTTP/1.1 keep-alive sem
        # enquadramento deixaria um cliente cru travado esperando mais bytes depois do [DONE]).
        self.close_connection = True
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()

        def manda(delta=None, fim=False):
            d = {"id": cid, "object": "chat.completion.chunk", "model": model_id,
                 "choices": [{"index": 0, "delta": {} if fim else {"content": delta}, "finish_reason": "stop" if fim else None}]}
            self.wfile.write(f"data: {json.dumps(d, ensure_ascii=False)}\n\n".encode("utf-8"))

        # resposta já veio inteira (perguntar não faz stream): manda em pedaços para o cliente ver chegar
        passo = 400
        for i in range(0, len(resp), passo):
            manda(resp[i:i + passo])
        manda(fim=True)
        self.wfile.write(b"data: [DONE]\n\n")


class _ServidorExclusivo(ThreadingHTTPServer):
    """31/10 09h46 (pc1): o http.server liga SO_REUSEADDR, e no Windows isso deixa um 2º genspark_http escutar a MESMA
    porta junto com o 1º — os pedidos em andamento foram cortados (ECONNRESET na VPS) e o Sonnet entrou no lugar.
    Porta exclusiva: um 2º servidor falha ao subir em vez de dividir a porta. Reiniciar = reiniciar_front.ps1."""
    allow_reuse_address = False

    def server_bind(self):
        import socket
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def main():
    srv = _ServidorExclusivo(("127.0.0.1", PORTA), H)
    print(f"genspark_http em http://127.0.0.1:{PORTA}  (modelos: {', '.join(MODELOS)}; vagas Genspark {VAGAS})", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
