#!/usr/bin/env python3
"""gemini_llm.py — Geração de texto e visão via Gemini (generateContent).

Usado como motor de descrição de painéis (visão) e narração quando o proxy
do Claude está fora. Reusa o pool de chaves Gemini do gemini_tts (26+ chaves).

Rotação DUPLA: chaves + modelos. Cada modelo free tier tem quota separada,
então alternar entre eles multiplica o throughput disponível.

Modelos suportados (todos com suporte a visão):
  - gemini-2.0-flash   (rápido, quota padrão)
  - gemini-1.5-flash   (quota mais generosa no free tier)
  - gemini-2.5-flash   (mais recente, quota separada)
"""
import base64
import json
import os
import time
import urllib.request
import urllib.error

import gemini_tts  # reusa pick_gemini_key / mark_key_ok / mark_key_error / bump_key_fila
import subprocess
import tempfile

# ─── Registro persistente de saúde dos modelos ──────────────────────────────
from pathlib import Path as _Path
_HEALTH_FILE = _Path(__file__).resolve().parent.parent / "workspace" / "model_health.json"

def _load_health():
    """Carrega registro de saúde dos modelos (falhas persistentes)."""
    if _HEALTH_FILE.exists():
        try:
            return json.loads(_HEALTH_FILE.read_text())
        except:
            pass
    return {}

def _save_health(data):
    """Salva registro de saúde."""
    _HEALTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    _HEALTH_FILE.write_text(json.dumps(data, indent=2))

def _record_model_failure(model, error_code, error_msg=""):
    """Registra falha de um modelo. Se acumular muitas falhas, desativa."""
    health = _load_health()
    if model not in health:
        health[model] = {"failures": 0, "last_success": None, "last_failure": None, "disabled": False, "errors": []}

    entry = health[model]
    entry["failures"] += 1
    entry["last_failure"] = time.time()
    # Guarda últimos 5 erros pra análise
    entry["errors"] = (entry.get("errors", []) + [{"code": error_code, "msg": error_msg[:100], "ts": time.time()}])[-5:]

    # Desativar se: 403 (sem acesso) ou 404 (não existe) — esses nunca vão funcionar
    if error_code in (403, 404):
        entry["disabled"] = True
        entry["reason"] = f"HTTP {error_code} permanente"
        _log(f"  🚫 Modelo {model} DESATIVADO (HTTP {error_code})")
    # Desativar se: 5+ falhas em horários diferentes (pelo menos 1h entre primeira e última)
    elif entry["failures"] >= 5:
        errors = entry.get("errors", [])
        if len(errors) >= 2:
            span = errors[-1]["ts"] - errors[0]["ts"]
            if span > 3600:  # falhas em >1h de intervalo = modelo inviável
                entry["disabled"] = True
                entry["reason"] = f"{entry['failures']} falhas em {span/3600:.1f}h"
                _log(f"  🚫 Modelo {model} DESATIVADO ({entry['failures']} falhas em {span/3600:.1f}h)")

    _save_health(health)

def _record_model_success(model):
    """Registra sucesso de um modelo — reseta contadores de falha."""
    health = _load_health()
    if model not in health:
        health[model] = {"failures": 0, "last_success": None, "last_failure": None, "disabled": False, "errors": []}
    health[model]["failures"] = 0
    health[model]["last_success"] = time.time()
    health[model]["errors"] = []
    _save_health(health)

def _get_active_models(pool):
    """Retorna modelos do pool que NÃO estão desativados."""
    health = _load_health()
    active = [m for m in pool if not health.get(m, {}).get("disabled", False)]
    if not active:
        # Se todos desativados, reativar os com menos falhas (reset)
        _log("  ⚠ Todos os modelos desativados! Reativando pool completo.")
        for m in pool:
            if m in health:
                health[m]["disabled"] = False
                health[m]["failures"] = 0
        _save_health(health)
        return pool
    return active


# ─── Pool de modelos de visão (cada um com quota free tier independente) ─────
VISION_MODELS = [
    # ▸ Confirmados com visão + quota AGORA (key[20] funcional)
    "gemini-flash-lite-latest",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    # ▸ Modelos especializados em IMAGEM (maior chance de sucesso em conteúdo sensível)
    "gemini-2.0-flash",
    "gemini-2.0-flash",
    "gemini-2.5-flash",
    # ▸ Quota exausta AGORA mas com pool separado (funciona ao resetar)
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.5-pro",
]
# Fallback se o env var não corresponder a nada na lista
MODEL = os.environ.get("GEMINI_LLM_MODEL", "gemini-2.0-flash")
if MODEL not in VISION_MODELS:
    VISION_MODELS.insert(0, MODEL)

# Estados de exaustão por (modelo, key_id): timestamp até quando respeitar
_model_exhausted = {}  # chave: f"{model}:{key_id}", valor: float(time.time() + cooldown)
# Duração do cooldown após 429 (segundos) — aumenta progressivamente
_model_exhausted_cooldown = 60  # inicial
_model_exhausted_idx = 0  # índice no grid models × keys

_SAFETY = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]


def _log(msg):
    gemini_tts.log(msg)


def _url(model, key):
    return f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"


def _pick_model_and_key():
    """Seleciona modelo e chave que não estejam exaustos/desativados."""
    global _model_exhausted_idx
    now = time.time()

    active_models_pool = _get_active_models(VISION_MODELS)
    n_active_models = len(active_models_pool)
    if not active_models_pool:
        _log("  ⚠ Nenhum modelo de visão ativo! Pool vazio.")
        return None, None, None # Sem modelos ativos

    # Tenta todas as combinações (models × keys)
    for _ in range(n_active_models * 50):  # máximo de tentativas
        kid, ktok = gemini_tts.pick_gemini_key()
        if not ktok:
            _log("  ✗ sem chaves gemini disponíveis (LLM)")
            return None, None, None

        model = active_models_pool[_model_exhausted_idx % n_active_models]
        _model_exhausted_idx += 1

        combo_key = f"{model}:{kid}"
        if combo_key in _model_exhausted and _model_exhausted[combo_key] > now:
            continue  # pula, tá em cooldown
        return model, kid, ktok

    # Fallback (se tudo exausto/desativado, pega a combinação mais antiga em cooldown)
    _log("  ⚠ Todos os modelos de visão exaustos/desativados. Usando fallback.")
    kid, ktok = gemini_tts.pick_gemini_key()
    if not ktok:
        _log("  ✗ sem chaves gemini disponíveis (LLM - fallback)")
        return None, None, None
    model = active_models_pool[_model_exhausted_idx % n_active_models] # pega um modelo ativo qualquer
    _model_exhausted_idx += 1
    return model, kid, ktok


def _mark_model_exhausted(model, key_id):
    """Marca combinação model+key como exausta por um período + registra falha persistente."""
    global _model_exhausted_cooldown
    combo_key = f"{model}:{key_id}"
    _model_exhausted[combo_key] = time.time() + _model_exhausted_cooldown
    _model_exhausted_cooldown = min(_model_exhausted_cooldown * 1.1, 300)
    # Registrar no arquivo persistente pra análise inteligente
    _record_model_failure(model, 429, f"quota exhausted key={key_id}")


_proxy_warned = False  # Log "proxy offline" apenas uma vez

# ─── Fallback via gateway OmniRoute (OpenAI-compatible, SSE) ─────────────────
# Quando TODAS as chaves Gemini diretas estão 429/mortas, cai aqui. O gateway
# já tem proxy próprio na base, então NÃO usamos proxy local. É OpenAI/SSE:
# POST /v1/chat/completions, Authorization: Bearer, resposta em chunks
# `data: {...}` com delta.content (ignoramos delta.reasoning_content).
# Só TEXTO puro — o gateway não faz visão nem TTS.
_GATEWAY_MODEL = os.environ.get("LLM_GATEWAY_MODEL", "antigravity/gemini-3-flash")  # 3.1-pro-high saiu do catálogo 16/10
_GATEWAY_ENABLED = os.environ.get("LLM_GATEWAY_FALLBACK", "1") != "0"
_gateway_warned = False


def _gateway_call(prompt, system=None, max_tokens=2048, temperature=1.0, timeout=120):
    """Fallback de texto via gateway OpenAI/SSE. Retorna texto ou None."""
    global _gateway_warned
    if not _GATEWAY_ENABLED:
        return None
    try:
        import claude_client
        cfg = claude_client._load_cfg()
    except Exception:
        cfg = None
    if not cfg or not cfg.get("base") or not cfg.get("key"):
        try:  # 21/10: os settings do Claude Code que o claude_client procura não existem aqui -> o gateway nunca era usado
            o = json.loads((_Path(__file__).resolve().parent.parent / "secrets" / "omniroute.json").read_text(encoding="utf-8"))
            cfg = {"base": o["base_url"], "key": o["api_key"]}
        except Exception:
            return None

    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    body = json.dumps({
        "model": _GATEWAY_MODEL,
        "messages": msgs,
        "stream": True,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }).encode("utf-8")

    url = cfg["base"].rstrip("/") + "/v1/chat/completions"
    # Retry curto: o gateway às vezes devolve 400/5xx transitório. Melhor 3
    # tentativas rápidas aqui do que cair no loop lento de chaves 429 (3min).
    last_err = ""
    for tent in range(3):
        req = urllib.request.Request(url, data=body, method="POST", headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cfg['key']}",
        })
        try:
            chunks = []
            with urllib.request.urlopen(req, timeout=timeout) as r:
                for raw_line in r:
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if not line or not line.startswith("data:"):
                        continue
                    payload = line[5:].strip()
                    if payload == "[DONE]":
                        break
                    try:
                        obj = json.loads(payload)
                    except Exception:
                        continue
                    delta = (obj.get("choices") or [{}])[0].get("delta", {})
                    piece = delta.get("content")  # ignora reasoning_content
                    if piece:
                        chunks.append(piece)
            text = "".join(chunks).strip()
            if text:
                _log(f"  ✔ Gemini LLM via gateway ({_GATEWAY_MODEL})")
                return text
            last_err = "resposta vazia"
        except Exception as e:
            last_err = str(e)[:100]
        time.sleep(2 * (tent + 1))
    if not _gateway_warned:
        _log(f"  ⚠ gateway fallback falhou (3x): {last_err}")
        _gateway_warned = True
    return None


def _call(parts, system=None, model=None, max_tokens=2048, temperature=1.0,
          max_attempts=12, timeout=120):
    """Chama generateContent com rotação de chave + modelo + retry. Retorna texto ou None."""
    global _proxy_warned
    fixed_model = model  # None = rotacionar automaticamente
    gen_config = {"temperature": temperature, "maxOutputTokens": max_tokens}

    delay = 2.0
    for attempt in range(max_attempts):
        # Rotação dupla: escolhe modelo + chave (pula combinações exaustas)
        if not fixed_model:
            m, kid, ktok = _pick_model_and_key()
            if not ktok:
                kid, ktok = gemini_tts.pick_gemini_key()
                if not ktok:
                    _log("  ✗ sem chaves gemini disponíveis (LLM)")
                    return _try_gateway_fallback(parts, system, max_tokens, temperature, timeout)
                m = VISION_MODELS[0] if VISION_MODELS else _GATEWAY_MODEL
        else:
            m = fixed_model
            kid, ktok = gemini_tts.pick_gemini_key()
            if not ktok:
                _log("  ✗ sem chaves gemini disponíveis (LLM)")
                return _try_gateway_fallback(parts, system, max_tokens, temperature, timeout)

        # Config específica do modelo
        cur_gen_config = dict(gen_config)
        if "2.5" in m or "-3" in m or "3." in m or "latest" in m:
            cur_gen_config["thinkingConfig"] = {"thinkingBudget": 0}

        body = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": cur_gen_config,
            "safetySettings": _SAFETY,
        }
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        data = json.dumps(body).encode("utf-8")

        url = _url(m, ktok)
        proxy = gemini_tts._get_next_proxy()

        raw = None
        used_proxy_direct = False
        if proxy:
            # Usa curl para QUALQUER proxy (SOCKS5, HTTP, HTTPS).
            # O corpo JSON pode conter imagens base64 (centenas de KB). No Windows,
            # passar isso via "-d <string>" estoura o limite de linha de comando (WinError 206),
            # então gravamos o corpo num arquivo temporário e usamos "--data-binary @arquivo".
            _bodyf = tempfile.NamedTemporaryFile("wb", suffix=".json", delete=False)
            _bodyf.write(data)
            _bodyf.close()
            curl_cmd = [
                "curl", "-sS", "--max-time", str(timeout),
                "-x", proxy,
                "-H", "Content-Type: application/json",
                "--data-binary", f"@{_bodyf.name}",
                url
            ]
            try:
                result = subprocess.run(curl_cmd, capture_output=True, text=True, check=True)
                try: os.unlink(_bodyf.name)
                except OSError: pass
                raw = json.loads(result.stdout)
                # Detectar erro HTTP retornado no JSON (curl retorna exit 0 mesmo com 429)
                if "error" in raw:
                    code = raw["error"].get("code", 0)
                    if code in (429, 403):
                        _mark_model_exhausted(m, kid)
                        _record_model_failure(m, code, raw.get("error", {}).get("message", "")[:80])
                        gemini_tts.mark_key_error(kid)
                        _log(f"  ⏳ Gemini LLM HTTP {code} (model={m}, key {kid}), trocando combo...")
                        time.sleep(delay); delay = min(delay * 1.5, 20)
                        continue
                    else:
                        _record_model_failure(m, code, raw.get("error", {}).get("message", "")[:80])
                        _log(f"  ✗ Gemini LLM HTTP {code}: {raw['error'].get('message','?')[:100]}")
                        time.sleep(1)
                        continue
                gemini_tts.mark_key_ok(kid)
                _record_model_success(m)
                used_proxy_direct = True
            except (subprocess.CalledProcessError, json.JSONDecodeError) as err:
                try: os.unlink(_bodyf.name)
                except OSError: pass
                err_str = str(err)
                stderr = getattr(err, 'stderr', '') or ''
                if isinstance(err, json.JSONDecodeError) or "JSON" in err_str:
                    # curl rodou mas resposta não é JSON — provavelmente erro HTTP
                    if not _proxy_warned:
                        _log(f"  ⏳ Proxy {proxy[:40]}... resposta inválida, fallback direto...")
                        _proxy_warned = True
                elif "connect" in err_str.lower() or "connect" in stderr.lower() or \
                   "refused" in err_str.lower() or "refused" in stderr.lower():
                    if not _proxy_warned:
                        _log(f"  ⏳ Proxy offline ({proxy[:40]}...), fallback direto...")
                        _proxy_warned = True
                else:
                    _log(f"  ✗ Gemini LLM curl error ({proxy[:30]}...): {err_str[:120]}")
                    gemini_tts.bump_key_fila(kid)
                    time.sleep(delay)
                    delay = min(delay * 1.5, 20)
                    continue

        if not used_proxy_direct:
            # Usa urllib para HTTP/HTTPS direto ou com variáveis de ambiente (se proxy não for socks)
            # urllib.request automaticamente respeita HTTP_PROXY/HTTPS_PROXY se definidos no ambiente
            # Se o proxy SOCKS5 falhou, esta é a tentativa direta.
            req = urllib.request.Request(url, data=data,
                                         headers={"Content-Type": "application/json"}, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    raw = json.loads(r.read().decode("utf-8", errors="replace"))
                gemini_tts.mark_key_ok(kid)
            except urllib.error.HTTPError as e:
                code = e.code
                msg = e.read().decode("utf-8", errors="replace")[:160] if e.fp else str(e)
                if code in (429, 403):
                    _mark_model_exhausted(m, kid)
                    _record_model_failure(m, code, msg)
                    gemini_tts.mark_key_error(kid)
                    _log(f"  ⏳ Gemini LLM HTTP {code} (model={m}, key {kid}), trocando combo...")
                    time.sleep(delay); delay = min(delay * 1.5, 20)
                    continue
                if code in (500, 503, 529):
                    _record_model_failure(m, code, msg)
                    _log(f"  ⏳ Gemini LLM HTTP {code}, retry em {delay:.0f}s...")
                    time.sleep(delay); delay = min(delay * 1.5, 20)
                    continue
                _record_model_failure(m, code, msg)
                _log(f"  ✗ Gemini LLM HTTP {code}: {msg}")
                time.sleep(1)
                continue
            except Exception as e:
                _record_model_failure(m, "conn_err", str(e)[:80])
                _log(f"  ⏳ Gemini LLM conn err: {str(e)[:80]}")
                time.sleep(delay); delay = min(delay * 1.5, 20)
                continue

        if not raw: # Se raw é None, houve um erro que não foi tratado acima
            _record_model_failure(m, "no_raw_response", "Resposta vazia/invalida")
            gemini_tts.bump_key_fila(kid)
            time.sleep(delay); delay = min(delay * 1.5, 20)
            continue

        # Parse da resposta
        cands = raw.get("candidates", [])
        if not cands:
            # bloqueio de prompt ou vazio — retenta (pode ser transitório / outra chave)
            fb = raw.get("promptFeedback", {})
            block_reason = fb.get("blockReason", "?")
            _log(f"  ⚠ Gemini LLM sem candidates (block={block_reason}), retry...")
            gemini_tts.bump_key_fila(kid)
            # Se block_reason = "?", provavelmente é quota exausta, não safety
            # Marca modelo+chave como exausto e rota
            if block_reason == "?":
                _mark_model_exhausted(m, kid)
                gemini_tts.mark_key_error(kid)
                time.sleep(1)
                continue
            # Se é safety block real (SAFETY, OTHER), tentamos 5x e pulamos
            if block_reason in ("SAFETY", "OTHER"):
                safety_blocks = getattr(_call, '_safety_blocks', 0) + 1
                _call._safety_blocks = safety_blocks
                if safety_blocks >= 5:
                    _log(f"  ✗ Gemini LLM safety block persistente ({block_reason}), pulando...")
                    _call._safety_blocks = 0
                    return None
            time.sleep(1)
            continue
        cand = cands[0]
        parts_out = cand.get("content", {}).get("parts", [])
        text = "".join(p.get("text", "") for p in parts_out).strip()
        if text:
            gemini_tts.mark_key_ok(kid)
            gemini_tts.bump_key_fila(kid)
            _record_model_success(m)
            return text
        # finishReason SAFETY ou vazio → tentar próxima chave/atempt
        _log(f"  ⚠ Gemini LLM resposta vazia (finish={cand.get('finishReason','?')})")
        gemini_tts.bump_key_fila(kid)
        time.sleep(1)

    # Esgotou as chaves Gemini diretas. Se for TEXTO puro (sem imagem), tenta o
    # gateway OpenAI/SSE como último fallback. Visão não passa pelo gateway.
    return _try_gateway_fallback(parts, system, max_tokens, temperature, timeout)


def _try_gateway_fallback(parts, system, max_tokens, temperature, timeout):
    """Último fallback: se for texto puro (sem imagem), tenta o gateway. Senão None."""
    if not all("inline_data" not in p for p in parts):
        return None  # visão não passa pelo gateway
    prompt = "\n".join(p.get("text", "") for p in parts if p.get("text"))
    if not prompt.strip():
        return None
    _log("  ↪ chaves Gemini esgotadas, tentando gateway...")
    return _gateway_call(prompt, system=system, max_tokens=max_tokens,
                         temperature=temperature, timeout=timeout)


def generate_text(prompt, system=None, prefer_gateway=None, **kw):
    """Gera texto a partir de um prompt (+ system opcional).

    prefer_gateway: se True (ou env LLM_GATEWAY_FIRST=1), tenta o gateway ANTES
    das chaves Gemini diretas — útil quando se sabe que as chaves estão saturadas
    (evita ~4min de loop 429 por chamada). Cai nas chaves diretas se o gateway falhar.
    """
    if prefer_gateway is None:
        # Default: gateway PRIMEIRO (sem proxy, gemini-3.1-pro-high). Chaves+proxy
        # só como fallback se o gateway falhar. LLM_GATEWAY_FIRST=0 inverte.
        prefer_gateway = os.environ.get("LLM_GATEWAY_FIRST", "1") == "1"
    if prefer_gateway:
        out = _gateway_call(prompt, system=system,
                            max_tokens=kw.get("max_tokens", 2048),
                            temperature=kw.get("temperature", 1.0),
                            timeout=kw.get("timeout", 120))
        if out:
            return out
    return _call([{"text": prompt}], system=system, **kw)


def describe_image(image_bytes, prompt, mime="image/jpeg", **kw):
    """Descreve UMA imagem (visão)."""
    b64 = base64.b64encode(image_bytes).decode()
    parts = [{"text": prompt}, {"inline_data": {"mime_type": mime, "data": b64}}]
    return _call(parts, **kw)


def describe_images(images_bytes, prompt, mime="image/jpeg", **kw):
    """Descreve VÁRIAS imagens numa chamada (batch). images_bytes: lista de bytes.

    O prompt deve pedir resposta numerada (1. 2. ...).
    """
    parts = [{"text": prompt}]
    for i, b in enumerate(images_bytes):
        parts.append({"text": f"{i+1}."})
        parts.append({"inline_data": {"mime_type": mime,
                                      "data": base64.b64encode(b).decode()}})
    return _call(parts, **kw)


def generate_from_images(images_bytes, prompt, system=None, mime="image/jpeg", **kw):
    """Olha VÁRIAS imagens (rotuladas 'Painel N:') e gera texto/JSON numa só chamada.

    Usado pra FUSÃO visão+narração: o Gemini lê os painéis e já escreve o roteiro,
    economizando as chamadas separadas de descrição.
    """
    parts = [{"text": prompt}]
    for i, b in enumerate(images_bytes):
        parts.append({"text": f"Painel {i+1}:"})
        parts.append({"inline_data": {"mime_type": mime,
                                      "data": base64.b64encode(b).decode()}})
    return _call(parts, system=system, **kw)


if __name__ == "__main__":
    # Teste rápido: texto
    print("Teste texto:", generate_text("Responda só: funcionando", max_tokens=20))
