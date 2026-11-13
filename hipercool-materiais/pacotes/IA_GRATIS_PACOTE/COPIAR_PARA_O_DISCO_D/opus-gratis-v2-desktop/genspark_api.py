# -*- coding: utf-8 -*-
r"""genspark_api.py — peças COMPARTILHADAS pelos dois modos "sem robotizar a tela".

O chat do Genspark é um `POST https://www.genspark.ai/api/agent/ask_proxy` (resposta SSE). O corpo exige
um `g_recaptcha_token` novo a cada mensagem e o pedido passa por Cloudflare. Dois modos usam estas peças:

  - genspark_pagina.py   (modo PÁGINA)  — manda o fetch de DENTRO da página logada (CDP). O token nasce do
    reCAPTCHA da própria página e o Cloudflare é satisfeito nativamente. Rápido, sem solver, sem burla.
  - genspark_http_puro.py (modo PURO)   — HTTP puro (curl_cffi impersonando Chrome) + cookies do cofre +
    token vindo de um serviço de captcha (decisão da dona 31/10; custa dinheiro). ZERO navegador.

Aqui ficam: a URL, o montador do corpo (igual ao capturado em captura/rede.json), o parser do SSE e o
guardador da config do reCAPTCHA (site key + action) descoberta ao vivo pela página.
"""
import json
import os
import re
import uuid
from pathlib import Path

BASE = Path(__file__).resolve().parent   # a própria pasta do projeto (portável: desktop, v2, pc1)
SEGREDOS = BASE / "segredos"
RECAPTCHA_CFG = SEGREDOS / "genspark_recaptcha.json"

ASK_URL = "https://www.genspark.ai/api/agent/ask_proxy"
MODELO_API = os.environ.get("GENSPARK_MODELO_API", "claude-opus-5-5")  # id do modelo no corpo do ask_proxy
# site key do reCAPTCHA Enterprise do ask_proxy (enterprise.js?render=...), descoberta ao vivo 31/10 na página.
SITEKEY_PADRAO = "6LfYyWcsAAAAAK8DUr6Oo1wHl2CJ5kKbO0AK3LIM"


def sitekey():
    return ler_recaptcha_cfg().get("sitekey") or SITEKEY_PADRAO
# o pedido capturado tinha busca ligada; dá pra desligar (mais rápido/determinístico) por env
HABILITAR_BUSCA = os.environ.get("GENSPARK_SEARCH", "1") not in ("0", "", "nao", "false")


def corpo_pedido(prompt, model=None, msg_id=None, is_private=True):
    """Monta o corpo JSON (dict) do ask_proxy, igual ao capturado — SEM o g_recaptcha_token (cada modo
    põe o seu). O chamador acrescenta body['g_recaptcha_token'] = <token> antes de enviar."""
    model = model or MODELO_API
    mid = msg_id or str(uuid.uuid4())
    msg = {"role": "user", "id": mid, "content": prompt, "pending": True,
           "sendStatus": "sending", "_deepDiveStateNegContent": prompt}
    return {
        "ai_chat_model": model,
        "ai_chat_enable_search": HABILITAR_BUSCA,
        "ai_chat_disable_personalization": False,
        "use_moa_proxy": False,
        "moa_models": [],
        "writingContent": None,
        "sas_ask_origin": "typed",
        "type": "ai_chat",
        "project_id": None,
        "messages": [msg],
        "user_s_input": prompt,
        "client_message_id": mid,
        "is_private": is_private,
        "push_token": "",
        "session_state": {"steps": [], "messages": [dict(msg)]},
        "last_seen_event_index": -1,
        "chat_session_id": None,
    }


# ─────────────────────────── parser do SSE ─────────────────────────────────
# O corpo da resposta é "event: message\ndata: {json}\n\n" repetido. O texto do modelo chega em pedaços
# (deltas) e/ou num campo acumulado. Este parser é TOLERANTE (o formato exato só se vê ao vivo): varre todos
# os data:{...}, tenta campos conhecidos de texto e fica com o maior acumulado; se só vierem deltas, concatena.
_CAMPOS_TEXTO = ("delta", "content", "text", "message", "answer", "token", "chunk", "value")


def _puxar_texto(obj, deltas, acumulados):
    """Procura texto de resposta recursivamente num objeto de evento. deltas: lista p/ concatenar;
    acumulados: lista de strings 'completas' candidatas (fica-se com a maior)."""
    if isinstance(obj, str):
        return
    if isinstance(obj, list):
        for x in obj:
            _puxar_texto(x, deltas, acumulados)
        return
    if not isinstance(obj, dict):
        return
    tipo = str(obj.get("type", "")).lower()
    # eventos de uso/erro/fim que não são texto do modelo
    for k in ("delta", "text", "content"):
        v = obj.get(k)
        if isinstance(v, str) and v:
            # delta = pedaço incremental; content/text costuma ser acumulado
            if k == "delta" or "delta" in tipo:
                deltas.append(v)
            else:
                acumulados.append(v)
    # campos aninhados comuns
    for k in ("data", "message", "choices", "value", "payload", "result", "response"):
        if k in obj:
            _puxar_texto(obj[k], deltas, acumulados)


def parse_sse(bruto):
    """Extrai o texto final de um corpo SSE do ask_proxy. Retorna (texto, eventos_crus:list[dict]).

    Schema do Genspark (confirmado ao vivo 31/10): o conteúdo do assistente chega em, nesta ordem de confiança:
      1) type=message_result -> message.content (texto completo e autoritativo, 1 por mensagem do assistente);
      2) type=message_field, field_name=content -> field_value (completo, por message_id);
      3) type=message_field_delta, field_name=content -> delta (pedaços, por message_id).
    CUIDADO: eventos type=project_field também têm field_value (título do projeto, status "FINISHED") — por isso
    NÃO se pega field_value genérico. Fallback final: varredura tolerante (_puxar_texto)."""
    eventos = []
    for bloco in re.split(r"\n\n+", bruto or ""):
        for linha in bloco.split("\n"):
            linha = linha.strip()
            if not linha.startswith("data:"):
                continue
            dado = linha[5:].strip()
            if not dado or dado == "[DONE]":
                continue
            try:
                eventos.append(json.loads(dado))
            except Exception:  # noqa: BLE001
                pass

    # 1) message_result.message.content (assistente) — junta na ordem se houver mais de uma mensagem
    partes = []
    for ev in eventos:
        if isinstance(ev, dict) and ev.get("type") == "message_result":
            msg = ev.get("message") or {}
            if isinstance(msg, dict) and msg.get("role") == "assistant":
                c = msg.get("content")
                if isinstance(c, str) and c.strip():
                    partes.append(c.strip())
    if partes:
        return "\n\n".join(partes).strip(), eventos

    # 2) message_field (field_name=content) — o último field_value por message_id é o completo
    pormsg = {}
    ordem = []
    for ev in eventos:
        if isinstance(ev, dict) and ev.get("type") == "message_field" and ev.get("field_name") == "content":
            v = ev.get("field_value")
            if isinstance(v, str):
                mid = ev.get("message_id")
                if mid not in pormsg:
                    ordem.append(mid)
                pormsg[mid] = v
    if pormsg:
        return "\n\n".join(pormsg[m] for m in ordem if pormsg.get(m)).strip(), eventos

    # 3) deltas de content por message_id
    deltas, ordem = {}, []
    for ev in eventos:
        if isinstance(ev, dict) and ev.get("type") == "message_field_delta" and ev.get("field_name") == "content":
            mid = ev.get("message_id")
            if mid not in deltas:
                deltas[mid] = []
                ordem.append(mid)
            deltas[mid].append(ev.get("delta") or "")
    if deltas:
        return "\n\n".join("".join(deltas[m]) for m in ordem).strip(), eventos

    # 4) fallback tolerante (formato mudou): varre tudo
    d, a = [], []
    for ev in eventos:
        _puxar_texto(ev, d, a)
    texto = max(a, key=len) if a else ""
    if d and len("".join(d)) > len(texto):
        texto = "".join(d)
    return texto.strip(), eventos


# ─────────────────────────── config do reCAPTCHA ───────────────────────────
# Frases do Genspark que NÃO são resposta do modelo, e sim "esta conta não tem Opus 5.5 no grátis" (pular a conta).
# Visto 31/10 ao rotear o pool: "Os modelos de ponta são um benefício da assinatura. Faça upgrade para desbloqueá-los."
SEM_OPUS_FRASES = ("faça upgrade", "faca upgrade", "upgrade para desbloque", "upgrade to unlock",
                   "benefício da assinatura", "beneficio da assinatura", "assine para desbloque",
                   "subscription to unlock", "upgrade to a paid")


def resposta_sem_opus(texto):
    """True se o texto é o aviso de 'modelo premium, faça upgrade' (conta sem Opus no grátis), não uma resposta."""
    b = (texto or "").lower()
    return any(f in b for f in SEM_OPUS_FRASES)


def classificar(corpo):
    """O que o Genspark devolveu de fato: None = resposta do modelo; "sem_credito" = créditos do dia acabaram;
    "sem_opus" = conta sem Opus no grátis. Medido 31/10: a resposta do modelo traz session_state._llm_model
    ("claude-opus-5-5") e _llm_usage; o aviso de crédito esgotado vem como mensagem do "assistente" SEM _llm_model, com
    session_state.consume_usage_quota_exceeded e link "fromurl=credit_exhausted" ("Você usou todos os seus créditos")."""
    texto, eventos = parse_sse(corpo)
    estados = [((ev.get("message") or {}).get("session_state") or {}) for ev in eventos
               if isinstance(ev, dict) and ev.get("type") == "message_result"]
    if any("consume_usage_quota_exceeded" in ss for ss in estados) or "credit_exhausted" in (corpo or ""):
        return "sem_credito"
    sem_modelo = estados and not any(ss.get("_llm_model") for ss in estados)
    if resposta_sem_opus(texto) and (sem_modelo or len(texto) < 300):
        return "sem_opus"
    if sem_modelo and any(f in texto.lower() for f in ("créditos", "creditos", "credits")):
        return "sem_credito"  # aviso de crédito com outra redação (não veio de modelo nenhum)
    return None


def ler_recaptcha_cfg():
    """{'sitekey':..., 'action':...} descoberto pela página (ou {} se ainda não)."""
    try:
        return json.loads(RECAPTCHA_CFG.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def salvar_recaptcha_cfg(sitekey, action=None):
    SEGREDOS.mkdir(exist_ok=True)
    cfg = ler_recaptcha_cfg()
    if sitekey:
        cfg["sitekey"] = sitekey
    if action:
        cfg["action"] = action
    RECAPTCHA_CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")
    return cfg
