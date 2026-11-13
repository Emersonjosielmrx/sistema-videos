#!/usr/bin/env python3
"""gemini_tts.py — TTS via Gemini 2.5 Flash com rotação de chave (Postgres).

Versão hipercool: paths locais ao projeto, mesma lógica de rotação do OpenClaw.

API pública:
    speak(text, voice="Kore", out_wav=...)  -> bool
    voice_for_persona(persona, kind="hipercool") -> voz Gemini
    list_voices()  -> lista de vozes prebuilt

CLI:
    gemini_tts.py --text "olá mundo" --voice Kore --out /tmp/t.wav
    gemini_tts.py --persona Bam --kind hipercool
"""
import argparse
import base64
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
PROJECT_DIR = Path(__file__).resolve().parent.parent
SECRETS = PROJECT_DIR / "secrets" / "postgres-fluxo-n8n.json"
VOICES_REGISTRY = PROJECT_DIR / "workspace" / "voices-registry.json"
LOG = PROJECT_DIR / "logs" / "gemini-tts.log"
LOG.parent.mkdir(parents=True, exist_ok=True)
VOICES_REGISTRY.parent.mkdir(parents=True, exist_ok=True)

MODEL = os.environ.get("GEMINI_TTS_MODEL", "gemini-3.1-flash-tts-preview")
TTS_MODELS = [
    # Modelo principal TTS (melhor qualidade/desempenho)
    "gemini-3.1-flash-tts-preview",
    # Modelos lite que aceitam responseModalities=['audio'] — quota separada!
    "gemini-3.1-flash-lite",
    # Fallbacks 2.5 (última opção — quota limitada, vozes diferentes)
    "gemini-2.5-flash-preview-tts",
    "gemini-2.5-pro-preview-tts",
]
_tts_model_idx = 0  # índice round-robin pros modelos TTS
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:streamGenerateContent"

REQUEST_TIMEOUT_S = int(os.environ.get("GEMINI_TTS_REQUEST_TIMEOUT_S", "120"))
FFMPEG_TIMEOUT_S = int(os.environ.get("GEMINI_TTS_FFMPEG_TIMEOUT_S", "30"))
RETRY_BACKOFF_S = float(os.environ.get("GEMINI_TTS_RETRY_BACKOFF_S", "1"))
KEY_COOLDOWN_S = int(os.environ.get("GEMINI_TTS_KEY_COOLDOWN_S", "300"))
# Teto da espera por quota: a janela por-minuto reseta em <=60s e há muitas chaves/modelos,
# então dormir 70s é desperdício. Cap baixo + rotação de modelo a cada 429 = menos ocioso.
MAX_QUOTA_WAIT_S = int(os.environ.get("GEMINI_TTS_MAX_QUOTA_WAIT_S", "12"))

# Pool de vozes prebuilt do Gemini TTS
# Femininas ORDENADAS por sensualidade (mais suave/sedutora/sussurrada primeiro).
# Obra +18 -> a escolha automática prefere as vozes mais sedutoras pras personagens.
VOICES_FEMALE = [
    "Achernar",      # Soft — muito sensual/intimista
    "Despina",       # Smooth — sedutora e aveludada
    "Sulafat",       # Warm — quente, aconchegante
    "Vindemiatrix",  # Gentle — suave, delicada
    "Aoede",         # Breezy — arejada, meio sussurrada
    "Erinome",       # Clear — neutra/clara
    "Leda",          # Youthful — jovem/fofa
    "Zephyr",        # Bright — energética
    "Pulcherrima",   # Forward — assertiva
    "Kore",          # Firm — madura/confiante (reservada p/ narradora)
]
# Subconjunto das MAIS sensuais (pra forçar escolha em obras +18)
VOICES_FEMALE_SENSUAL = ["Achernar", "Despina", "Sulafat", "Vindemiatrix", "Aoede"]
VOICES_MALE = [
    "Charon", "Puck", "Fenrir", "Orus", "Gacrux",
    "Iapetus", "Algenib", "Algieba", "Achird", "Sadachbia",
]
VOICES_PREBUILT = VOICES_FEMALE + VOICES_MALE

# Vozes reservadas pra narrador (não entram no auto-pool de personagens)
# Padrão: voz feminina madura/sedutora pra manhwa 18+
NARRATOR_VOICES = {"hipercool": "Kore", "manhwa": "Kore", "broll": "Kore"}
# Narrador masculino (quando --narrator-gender M): voz grave/madura
NARRATOR_VOICE_MALE = "Charon"

# Instrução de estilo pra momentos sensuais/+18 (prefixada ao texto do TTS).
# O Gemini TTS interpreta a diretiva inicial como estilo e NÃO a lê em voz alta.
SENSUAL_STYLE_PREFIX = "Narre com voz sensual, sussurrada e provocante, num tom ofegante e envolvente: "


def _is_male(voice):
    return voice in VOICES_MALE


def _is_female(voice):
    return voice in VOICES_FEMALE


def log(msg):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] {msg}"
    print(line, file=sys.stderr)
    with LOG.open("a") as f:
        f.write(line + "\n")


# ─── Postgres: rotação de chave Gemini ──────────────────────────────────────
_pg_conn = None
_local_keys = None  # Fallback: chaves em JSON local
_local_key_idx = 0


def _load_local_keys():
    """Carrega chaves de secrets/gemini_keys.json (fallback sem PG)."""
    global _local_keys
    keys_file = PROJECT_DIR / "secrets" / "gemini_keys.json"
    if keys_file.exists():
        _local_keys = json.loads(keys_file.read_text())
    else:
        _local_keys = []
    return _local_keys


def _pg():
    global _pg_conn
    if _pg_conn is None or _pg_conn.closed:
        import psycopg2
        creds = json.loads(SECRETS.read_text())
        host = os.environ.get("PG_HOST", "127.0.0.1")
        _pg_conn = psycopg2.connect(
            host=host, port=creds["port"], dbname=creds["dbname"],
            user=creds["user"], password=creds["password"], connect_timeout=10,
        )
        _pg_conn.autocommit = True
    return _pg_conn


def pick_gemini_key():
    """Retorna (id, token) da chave gemini. Tenta PG, fallback pra JSON local."""
    global _local_key_idx
    # Tentar PostgreSQL primeiro
    try:
        cur = _pg().cursor()
        cur.execute("""
            SELECT id, token FROM nova_lista_de_chaves_2
            WHERE tipo='gemini'
              AND (
                status IS NULL
                OR status NOT IN ('erro', 'expired')
                OR COALESCE("data-erro-inteiro", 0) < EXTRACT(epoch FROM now())::int - %s
              )
              AND status IS DISTINCT FROM 'expired'
            ORDER BY
              CASE WHEN status='erro' THEN 1 ELSE 0 END,
              fila ASC NULLS FIRST,
              id ASC
            LIMIT 1
        """, (KEY_COOLDOWN_S,))
        row = cur.fetchone()
        if row:
            return (row[0], row[1])
    except Exception:
        pass

    # Fallback: JSON local (round-robin)
    if _local_keys is None:
        _load_local_keys()
    if not _local_keys:
        return (None, None)
    key = _local_keys[_local_key_idx % len(_local_keys)]
    _local_key_idx += 1
    return (key["id"], key["token"])


def bump_key_fila(key_id):
    try:
        cur = _pg().cursor()
        cur.execute(
            "UPDATE nova_lista_de_chaves_2 SET fila = COALESCE(fila,0) + 1 WHERE id=%s",
            (key_id,),
        )
    except Exception:
        pass


def mark_key_error(key_id):
    try:
        cur = _pg().cursor()
        cur.execute(
            "UPDATE nova_lista_de_chaves_2 SET status='erro', \"data-erro-inteiro\"=EXTRACT(epoch FROM now())::int "
            "WHERE id=%s",
            (key_id,),
        )
    except Exception:
        pass


def mark_key_ok(key_id):
    try:
        cur = _pg().cursor()
        cur.execute(
            "UPDATE nova_lista_de_chaves_2 SET status='ok' WHERE id=%s",
            (key_id,),
        )
    except Exception:
        pass


# ─── Voz por persona (persistente) ──────────────────────────────────────────
def _load_registry():
    if VOICES_REGISTRY.exists():
        try:
            return json.loads(VOICES_REGISTRY.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            # Arquivo legado gravado em cp1252 (execução antiga sem PYTHONUTF8);
            # lê, normaliza e regrava em utf-8 pra não quebrar de novo.
            reg = json.loads(VOICES_REGISTRY.read_text(encoding="cp1252"))
            VOICES_REGISTRY.write_text(
                json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")
            return reg
    return {"personas": {}, "narrators": NARRATOR_VOICES.copy()}


def _save_registry(reg):
    VOICES_REGISTRY.write_text(
        json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")


def voice_for_persona(persona, gender=None, kind="hipercool"):
    """Retorna a voz Gemini atribuída a esse persona.
    Mantém vozes consistentes entre capítulos (registry persistente).
    """
    persona = (persona or "").strip()
    # Limpar anotações como "(pensando)", "[off]", etc.
    persona = re.sub(r"\s*[\(\[\{].*?[\)\]\}]", "", persona).strip()
    if not persona:
        return NARRATOR_VOICES.get(kind, "Charon")
    reg = _load_registry()
    reg.setdefault("personas", {})

    # narrador: voz fixa por kind (ou voz masculina madura se gender=M)
    if persona.lower() in ("narrador", "narrator", "voz off", "voz_off"):
        if (gender or "").upper() == "M":
            v = NARRATOR_VOICE_MALE
        else:
            v = reg.get("narrators", {}).get(kind, NARRATOR_VOICES.get(kind, "Kore"))
        reg["personas"][persona] = {"voice": v, "gender": "F" if _is_female(v) else "M", "is_narrator": True}
        _save_registry(reg)
        return v

    # já existe? (match exato)
    entry = reg["personas"].get(persona)
    if isinstance(entry, str):
        reg["personas"][persona] = {"voice": entry, "gender": "F" if _is_female(entry) else "M"}
        _save_registry(reg)
        return entry
    if isinstance(entry, dict) and entry.get("voice"):
        return entry["voice"]

    # match aproximado: "Joon", "Joon-seo", "Protagonista Joon" -> mesma voz.
    # Estratégia: compara TOKENS de nome distintivos (ignora palavras genéricas).
    # Se compartilham um token de nome distinto E mesmo gênero -> mesma persona.
    import difflib
    g = (gender or "").upper()
    _STOP = {"protagonista", "personagem", "narrador", "narradora", "garoto",
             "garota", "menino", "menina", "rapaz", "moca", "moça", "homem",
             "mulher", "jovem", "senhor", "senhora", "the", "de", "da", "do"}

    def _name_tokens(name):
        toks = re.split(r"[^a-zA-ZÀ-ÿ]+", name.lower())
        return {t for t in toks if len(t) >= 3 and t not in _STOP}

    ptokens = _name_tokens(persona)
    match_name = None
    for name, e in reg["personas"].items():
        if not (isinstance(e, dict) and e.get("voice") and not e.get("is_narrator")):
            continue
        if g and e.get("gender") and e.get("gender") != g:
            continue
        ntokens = _name_tokens(name)
        # token de nome distintivo em comum, ou nomes muito parecidos (difflib > 0.8)
        if (ptokens & ntokens) or difflib.SequenceMatcher(None, persona.lower(), name.lower()).ratio() > 0.8:
            match_name = name
            break

    if match_name:
        v = reg["personas"][match_name]["voice"]
        reg["personas"][persona] = {"voice": v,
                                    "gender": reg["personas"][match_name].get("gender", g or "M"),
                                    "alias_de": match_name}
        _save_registry(reg)
        log(f"  persona {persona!r} ≈ {match_name!r} -> mesma voz {v}")
        return v

    # novo: escolhe pool por gênero
    if g == "F":
        pool = VOICES_FEMALE
    elif g == "M":
        pool = VOICES_MALE
    else:
        pool = VOICES_PREBUILT

    used = {e.get("voice") if isinstance(e, dict) else e
            for e in reg["personas"].values()}
    used |= set(NARRATOR_VOICES.values())
    free = [v for v in pool if v not in used]
    if not free:
        from collections import Counter
        cnt = Counter(e.get("voice") if isinstance(e, dict) else e
                       for e in reg["personas"].values())
        free = [v for v in pool if v not in NARRATOR_VOICES.values()]
        free.sort(key=lambda v: cnt.get(v, 0))
        if not free:
            free = pool[:]
    chosen = free[0]
    reg["personas"][persona] = {
        "voice": chosen,
        "gender": "F" if _is_female(chosen) else "M",
        "first_seen": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    _save_registry(reg)
    log(f"  novo persona {persona!r} (gênero={g or '?'}) -> voz {chosen}")
    return chosen


# ─── Proxy rotativo (evita rate limit por IP) ─────────────────────────────────
PROXY_ENABLED = os.environ.get("GEMINI_TTS_PROXY_ENABLED", "1") == "1"
PROXY_LIST_FILE = PROJECT_DIR / "secrets" / "proxies.txt"
_proxy_list = []
_proxy_idx = 0
_proxy_dead = False  # vira True se o proxy (ex: túnel SOCKS5) cair -> usa conexão direta


def _load_proxies():
    """Carrega lista de proxies de secrets/proxies.txt.
    Formato: http://ip:port ou http://<USUARIO>:<SEGREDO_REMOVIDO>@ip:port (um por linha)
    """
    global _proxy_list
    if PROXY_LIST_FILE.exists():
        lines = PROXY_LIST_FILE.read_text(encoding="utf-8", errors="replace").strip().splitlines()
        _proxy_list = [l.strip() for l in lines if l.strip() and not l.startswith("#")]
    return _proxy_list


def _get_next_proxy():
    """Retorna próximo proxy da lista (rotação round-robin). None se sem proxy."""
    global _proxy_idx
    if not PROXY_ENABLED or _proxy_dead:
        return None
    if not _proxy_list:
        _load_proxies()
    if not _proxy_list:
        return None
    proxy = _proxy_list[_proxy_idx % len(_proxy_list)]
    _proxy_idx += 1
    return proxy


# ─── API call ───────────────────────────────────────────────────────────────
def _get_tts_url(api_key):
    """Retorna URL do modelo TTS com rotação round-robin."""
    global _tts_model_idx
    model = TTS_MODELS[_tts_model_idx % len(TTS_MODELS)]
    return f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?key={api_key}", model


def _rotate_tts_model():
    """Avança pro próximo modelo TTS (chamado após quota 429)."""
    global _tts_model_idx
    _tts_model_idx += 1
    model = TTS_MODELS[_tts_model_idx % len(TTS_MODELS)]
    log(f"  [*] TTS rotacionando modelo -> {model}")


def _request_gemini(text, voice, api_key, timeout=REQUEST_TIMEOUT_S):
    """POST pra endpoint Gemini TTS. Retorna (pcm_bytes, "ok") ou (None, "quota"/"other")."""
    body = {
        "contents": [{"role": "user", "parts": [{"text": text}]}],
        "generationConfig": {
            "responseModalities": ["audio"],
            "temperature": 1,
            "speech_config": {
                "voice_config": {
                    "prebuilt_voice_config": {"voice_name": voice}
                }
            },
        },
    }
    url, tts_model = _get_tts_url(api_key)
    proxy = _get_next_proxy()

    # Se proxy SOCKS5 — usar curl (urllib não suporta socks nativamente)
    if proxy and proxy.startswith("socks"):
        result = _request_via_curl(url, body, voice, proxy, timeout)
        if result[1] == "proxy_dead":
            # Proxy caiu -> desliga pro resto da sessão e segue direto (sem proxy)
            global _proxy_dead
            _proxy_dead = True
            log("  [!] proxy SOCKS5 fora do ar — usando conexão DIRETA no resto da sessão")
            proxy = None  # cai pro path direto abaixo
        else:
            return result

    # Request normal (com ou sem proxy HTTP), COM FAILOVER:
    # se o proxy dá erro de CONEXÃO (não chegou no Google), tenta o próximo
    # proxy da lista. HTTPError (429/403/etc) = chegou no Google -> NÃO troca de
    # proxy (é quota/chave, resolvido no loop de speak()). Só troca em falha de rede.
    data = json.dumps(body).encode("utf-8")
    n_proxies = len(_proxy_list) if _proxy_list else 1
    max_proxy_tries = min(n_proxies, 4) if proxy else 1  # sem proxy: 1 tentativa direta

    for ptry in range(max_proxy_tries):
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json"}, method="POST")
        if proxy:
            opener = urllib.request.build_opener(
                urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
        else:
            opener = urllib.request.build_opener()

        try:
            with opener.open(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
            return _parse_gemini_response(raw, voice)
        except urllib.error.HTTPError as e:
            # Chegou no Google (proxy funcionou). É quota/chave, não erro de proxy.
            msg = e.read().decode("utf-8", errors="replace") if e.fp else str(e)
            log(f"  HTTP {e.code} voice={voice}: {msg[:200]}")
            if e.code in (429, 403, 400, 503):
                return (None, "quota")
            raise
        except Exception as e:
            # Erro de CONEXÃO (proxy morto/timeout de rede) -> tenta o próximo proxy.
            log(f"  conn err (proxy tentativa {ptry+1}/{max_proxy_tries}): {e}")
            if proxy and ptry < max_proxy_tries - 1:
                proxy = _get_next_proxy()
                continue
            return (None, "other")

    return (None, "other")


def _request_via_curl(url, body, voice, proxy, timeout):
    """Faz request via curl (suporta SOCKS5 proxy)."""
    import subprocess as _sp
    body_json = json.dumps(body)
    cmd = [
        "curl", "-s", "--max-time", str(timeout),
        "-x", proxy,
        "-H", "Content-Type: application/json",
        "-d", body_json,
        url,
    ]
    try:
        result = _sp.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
        if result.returncode != 0:
            # curl não conseguiu conectar (ex: túnel SOCKS5 caiu) -> proxy morto
            log(f"  curl err (proxy morto?): {result.stderr[:100]}")
            return (None, "proxy_dead")
        raw = result.stdout
        if not raw:
            return (None, "other")
        # Check for HTTP errors in response
        if '"error"' in raw and '"429"' in raw:
            log(f"  HTTP 429 voice={voice}: {raw[:200]}")
            return (None, "quota")
        if '"error"' in raw and ('"403"' in raw or '"400"' in raw):
            log(f"  HTTP err voice={voice}: {raw[:200]}")
            return (None, "quota")
        return _parse_gemini_response(raw, voice)
    except Exception as e:
        log(f"  curl exception: {e}")
        return (None, "other")


def _parse_gemini_response(raw, voice):
    """Parse streaming JSON response do Gemini TTS."""

    # Parse streaming JSON response
    try:
        chunks = json.loads(raw)
    except json.JSONDecodeError:
        chunks = []
        for m in re.finditer(r"\{[^{}]*\"candidates\"[^{}]*\}", raw, re.DOTALL):
            try:
                chunks.append(json.loads(m.group(0)))
            except Exception:
                pass
    if not chunks:
        log(f"  empty response: {raw[:200]}")
        return (None, "other")

    pcm_b64_parts = []
    for c in chunks:
        try:
            parts = c["candidates"][0]["content"]["parts"]
            for p in parts:
                ind = p.get("inlineData") or p.get("inline_data")
                if ind and ind.get("data"):
                    pcm_b64_parts.append(ind["data"])
        except (KeyError, IndexError, TypeError):
            continue
    if not pcm_b64_parts:
        log(f"  no inlineData in chunks (n={len(chunks)})")
        return (None, "other")

    pcm = b"".join(base64.b64decode(p) for p in pcm_b64_parts)
    return (pcm, "ok")


def speak(text, voice="Kore", out_wav=None, max_attempts=int(os.environ.get("GEMINI_TTS_MAX_ATTEMPTS", "25"))):
    """Sintetiza `text` na `voice`. Salva WAV (44.1k/2ch) em out_wav.
    Retorna True/False. Faz rotação de chave em quota/auth error.

    Se esgotar todas as tentativas por quota, dá um sleep extra de 60s
    (pro resfriamento fazer efeito) antes de retornar False.
    """
    text = (text or "").strip()
    if len(text) < 4:
        return False
    out_wav = Path(out_wav)
    consecutive_quota = 0  # conta quantas 429 seguidas
    for attempt in range(max_attempts):
        kid, ktok = pick_gemini_key()
        if not ktok:
            log("  [X] sem chaves gemini disponíveis")
            return False
        log(f"  -> key id={kid} voice={voice} text={text[:60]!r}")
        try:
            pcm, status = _request_gemini(text, voice, ktok)
        except Exception as e:
            log(f"  [X] erro irrecuperável: {e}")
            return False
        if status == "quota":
            consecutive_quota += 1
            mark_key_error(kid)
            # Rotaciona modelo TTS a CADA 429: tenta um pool de quota separado na hora
            # (3.1-flash-lite e os 2.5-tts têm cotas próprias) em vez de ficar dormindo.
            _rotate_tts_model()
            # Backoff curto e LIMITADO (cap em MAX_QUOTA_WAIT_S). A janela por-minuto
            # reseta em <=60s; com pick_gemini_key girando chave + modelo girando pool,
            # achamos um combo livre rápido sem desperdiçar ~70s ociosos.
            wait = min(RETRY_BACKOFF_S * (1 + consecutive_quota), MAX_QUOTA_WAIT_S)
            log(f"  ⏳ quota atingida (#{consecutive_quota} consecutiva), trocando combo, aguardando {wait:.0f}s...")
            time.sleep(wait)
            continue
        consecutive_quota = 0  # reset se não foi quota
        if pcm is None:
            bump_key_fila(kid)
            time.sleep(RETRY_BACKOFF_S)
            continue
        # Sucesso
        mark_key_ok(kid)
        bump_key_fila(kid)
        # PCM s16le 24k mono -> WAV via ffmpeg
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-f", "s16le", "-ar", "24000", "-ac", "1",
                 "-i", "pipe:0", "-ar", "44100", "-ac", "2", str(out_wav)],
                input=pcm, check=True, capture_output=True, timeout=FFMPEG_TIMEOUT_S,
            )
            log(f"  [OK] wrote {out_wav.name} ({out_wav.stat().st_size//1024} KB)")
            return True
        except subprocess.CalledProcessError as e:
            log(f"  ffmpeg ERR: {e.stderr.decode(errors='replace')[-200:]}")
            return False
    log("  [X] esgotou max_attempts após esgotar chaves/quota")
    # Se saiu por quota, pequena espera pra resfriar antes de devolver False
    if consecutive_quota > 0:
        wait = min(20, MAX_QUOTA_WAIT_S + 8)
        log(f"  🔥 cooling final de {wait}s antes de devolver False")
        time.sleep(wait)
    return False


def list_voices():
    return VOICES_PREBUILT


# ─── CLI ────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--text", help="Texto a sintetizar")
    p.add_argument("--voice", default="Kore",
                   help=f"Voz (default: Kore). Opções: {', '.join(VOICES_PREBUILT)}")
    p.add_argument("--out", help="Arquivo .wav de saída")
    p.add_argument("--persona", help="Nome do personagem")
    p.add_argument("--gender", choices=["M", "F"])
    p.add_argument("--kind", default="hipercool")
    p.add_argument("--list-voices", action="store_true")
    p.add_argument("--show-registry", action="store_true")
    args = p.parse_args()

    if args.list_voices:
        print("FEMALE:")
        for v in VOICES_FEMALE:
            print(f"  {v}")
        print("MALE:")
        for v in VOICES_MALE:
            print(f"  {v}")
        return

    if args.show_registry:
        print(json.dumps(_load_registry(), ensure_ascii=False, indent=2))
        return

    voice = args.voice
    if args.persona:
        voice = voice_for_persona(args.persona, gender=args.gender, kind=args.kind)
        print(f"persona={args.persona!r} gender={args.gender} -> voz={voice}")
        if not args.text:
            return

    if not args.text or not args.out:
        p.error("forneça --text e --out (ou só --persona pra ver atribuição)")
    ok = speak(args.text, voice=voice, out_wav=args.out)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
