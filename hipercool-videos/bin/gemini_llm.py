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
        _log("  [!] Todos os modelos desativados! Reativando pool completo.")
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
    "gemini-3.1-flash-lite",
    "gemini-3.1-flash-lite-preview",
    "gemini-3-flash-preview",
    "gemini-3.1-pro-preview",
    # Removidos em 2026-10-13 (HTTP 404 "no longer available"): gemini-2.0-flash(-lite),
    # gemini-2.5-flash(-lite), gemini-2.5-pro, gemini-3.1-pro — só atrasavam o rodízio.
    # Removidos em 2026-10-16: gemini-3.1-flash-image, gemini-3.1-flash-image-preview e
    # gemini-2.5-flash-image. São modelos de GERAR imagem, não de ler; entraram aqui na esperança
    # de aguentarem melhor conteúdo sensível e nunca responderam UMA vez (workspace/model_health.json:
    # last_success = null nos três, 49 tentativas desde 13/10, todas 429). Como o rodízio é redondo,
    # eles ficavam com 3 de cada 8 tentativas da visão — cada uma com ida à API mais sleep crescente
    # (2 s -> 20 s). Foi o grosso da tempestade de 429 do cap 11 (15/10 22:46-22:48). Só voltam com
    # prova de que devolvem TEXTO.
    # Em observação: gemini-3.1-pro-preview está 0 de 18 (a quota pro do free tier é mínima). Se
    # continuar sem nenhum last_success na próxima leva, sai também.
]
# Fallback se o env var não corresponder a nada na lista
MODEL = os.environ.get("GEMINI_LLM_MODEL", "gemini-3.1-flash-lite")
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


def _uma_linha(msg, n=120):
    """Erro da API numa linha só. O corpo do 400 vem em JSON formatado e espalhava 6 linhas sem
    carimbo de hora no log do capítulo (cap 11, 15/10) — impossível de achar com grep."""
    return " ".join(str(msg).split())[:n]


def _url(model, key):
    return f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"


def _pick_model_and_key():
    """Seleciona modelo e chave que não estejam exaustos/desativados."""
    global _model_exhausted_idx
    now = time.time()

    active_models_pool = _get_active_models(VISION_MODELS)
    n_active_models = len(active_models_pool)
    if not active_models_pool:
        _log("  [!] Nenhum modelo de visão ativo! Pool vazio.")
        return None, None, None # Sem modelos ativos

    # Tenta todas as combinações (models × keys)
    for _ in range(n_active_models * 50):  # máximo de tentativas
        kid, ktok = gemini_tts.pick_gemini_key()
        if not ktok:
            _log("  [X] sem chaves gemini disponíveis (LLM)")
            return None, None, None

        model = active_models_pool[_model_exhausted_idx % n_active_models]
        _model_exhausted_idx += 1

        combo_key = f"{model}:{kid}"
        if combo_key in _model_exhausted and _model_exhausted[combo_key] > now:
            continue  # pula, tá em cooldown
        return model, kid, ktok

    # Fallback (se tudo exausto/desativado, pega a combinação mais antiga em cooldown)
    _log("  [!] Todos os modelos de visão exaustos/desativados. Usando fallback.")
    kid, ktok = gemini_tts.pick_gemini_key()
    if not ktok:
        _log("  [X] sem chaves gemini disponíveis (LLM - fallback)")
        return None, None, None
    model = active_models_pool[_model_exhausted_idx % n_active_models] # pega um modelo ativo qualquer
    _model_exhausted_idx += 1
    return model, kid, ktok


def _mark_model_exhausted(model, key_id, msg="", code=429):
    """Marca combinação model+key como exausta por um período + registra falha persistente.

    16/10: quem trata o 429/403 chamava esta função E `_record_model_failure` logo depois, então
    cada 429 contava DUAS falhas — daí as linhas repetidas "DESATIVADO (19 falhas)" / "(20 falhas)"
    no cap 11. Com a conta dobrada o pool inteiro era desativado na metade do tempo e o
    `_get_active_models` reativava tudo em seguida, num vai-e-vem. Agora o registro é feito só aqui.
    """
    global _model_exhausted_cooldown
    combo_key = f"{model}:{key_id}"
    _model_exhausted[combo_key] = time.time() + _model_exhausted_cooldown
    _model_exhausted_cooldown = min(_model_exhausted_cooldown * 1.1, 300)
    # Registrar no arquivo persistente pra análise inteligente (com o código DE VERDADE: o 403
    # desativa o modelo de vez em `_record_model_failure`, o 429 não).
    _record_model_failure(model, code, _uma_linha(msg, 80) or f"quota exhausted key={key_id}")


_proxy_warned = False  # Log "proxy offline" apenas uma vez

def _call(parts, system=None, model=None, max_tokens=2048, temperature=1.0,
          max_attempts=6, timeout=120):
    """Chaves diretas (rotação) e, se todas falharem (429/bloqueio), os Gemini do proxy do Claude Code
    (claude_client.GEMINI_PROXY). Retorna texto ou None."""
    text = _call_direto(parts, system=system, model=model, max_tokens=max_tokens,
                        temperature=temperature, max_attempts=max_attempts, timeout=timeout)
    if text:
        return text
    if any(not p["inline_data"].get("mime_type", "").startswith("image/") for p in parts if "inline_data" in p):
        return None  # áudio/vídeo: o proxy (formato Anthropic) só aceita imagem
    try:
        import claude_client
        prompt = "\n".join(p["text"] for p in parts if "text" in p)
        imgs = [base64.b64decode(p["inline_data"]["data"]) for p in parts if "inline_data" in p]
        text = claude_client.gemini(prompt, imgs, system=system, max_tokens=max_tokens,
                                    temperature=min(temperature, 1.0))
        if text:
            _log("  [reserva] Gemini via proxy respondeu")
        return text
    except Exception as e:  # noqa: BLE001
        _log(f"  [X] reserva Gemini via proxy falhou: {str(e)[:120]}")
        return None


def _call_direto(parts, system=None, model=None, max_tokens=2048, temperature=1.0,
                 max_attempts=6, timeout=120):
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
                    _log("  [X] sem chaves gemini disponíveis (LLM)")
                    return None
                m = VISION_MODELS[0]
        else:
            m = fixed_model
            kid, ktok = gemini_tts.pick_gemini_key()
            if not ktok:
                _log("  [X] sem chaves gemini disponíveis (LLM)")
                return None

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
                        _mark_model_exhausted(m, kid, raw.get("error", {}).get("message", "")[:80], code)
                        gemini_tts.mark_key_error(kid)
                        _log(f"  ⏳ Gemini LLM HTTP {code} (model={m}, key {kid}), trocando combo...")
                        time.sleep(delay); delay = min(delay * 1.5, 20)
                        continue
                    else:
                        _record_model_failure(m, code, raw.get("error", {}).get("message", "")[:80])
                        _log(f"  [X] Gemini LLM HTTP {code} (model={m}, key {kid}): "
                             f"{_uma_linha(raw['error'].get('message', '?'))}")
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
                    _log(f"  [X] Gemini LLM curl error ({proxy[:30]}...): {err_str[:120]}")
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
                    _mark_model_exhausted(m, kid, msg, code)
                    gemini_tts.mark_key_error(kid)
                    _log(f"  ⏳ Gemini LLM HTTP {code} (model={m}, key {kid}), trocando combo...")
                    time.sleep(delay); delay = min(delay * 1.5, 20)
                    continue
                if code in (500, 503, 529):
                    _record_model_failure(m, code, msg)
                    _log(f"  ⏳ Gemini LLM HTTP {code} (model={m}, key {kid}), retry em {delay:.0f}s...")
                    time.sleep(delay); delay = min(delay * 1.5, 20)
                    continue
                _record_model_failure(m, code, msg)
                # 16/10: esta linha era só "HTTP 400: <corpo em 6 linhas>". Sem o modelo não dava
                # pra saber QUEM recusou — o 400 do cap 11 ("invalid argument") só foi atribuído ao
                # gemini-flash-lite-latest depois, cruzando com o model_health.json.
                _log(f"  [X] Gemini LLM HTTP {code} (model={m}, key {kid}): {_uma_linha(msg)}")
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
            _log(f"  [!] Gemini LLM sem candidates (block={block_reason}), retry...")
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
                    _log(f"  [X] Gemini LLM safety block persistente ({block_reason}), pulando...")
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
        # finishReason SAFETY ou vazio -> tentar próxima chave/atempt
        _log(f"  [!] Gemini LLM resposta vazia (finish={cand.get('finishReason','?')})")
        gemini_tts.bump_key_fila(kid)
        time.sleep(1)
    return None


def generate_text(prompt, system=None, **kw):
    """Gera texto a partir de um prompt (+ system opcional)."""
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


def transcribe_audio(audio_bytes, mime="audio/wav", prompt=None, **kw):
    """Transcreve UM audio em texto (ditado por voz). Reusa rotacao de chaves/modelos.

    Retorna so a transcricao literal em portugues, sem comentarios.
    """
    if prompt is None:
        prompt = ("Transcreva exatamente o que foi falado neste audio, em portugues do Brasil. "
                  "Responda SOMENTE com a transcricao literal: sem aspas, sem comentarios, "
                  "sem traducao, sem explicacao. Se nao houver fala, responda vazio.")
    b64 = base64.b64encode(audio_bytes).decode()
    parts = [{"text": prompt}, {"inline_data": {"mime_type": mime, "data": b64}}]
    return _call(parts, **kw)


if __name__ == "__main__":
    # Teste rápido: texto
    print("Teste texto:", generate_text("Responda só: funcionando", max_tokens=20))
