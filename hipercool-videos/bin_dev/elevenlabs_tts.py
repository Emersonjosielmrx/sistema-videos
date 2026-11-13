#!/usr/bin/env python3
"""elevenlabs_tts.py — Roteador de chaves ElevenLabs (narrador/dublador).

Gerencia VÁRIAS chaves da ElevenLabs com:
- rotação de chave por crédito disponível (10k/mês free; Starter desbloqueia library)
- controle de créditos via /v1/user/subscription (cacheado por chave)
- PROXY OBRIGATÓRIO (regra firme do usuário: nunca chamar sem proxy de IP, senão bloqueia)
- fallback: se nenhuma chave EL com crédito -> retorna False (caller usa Gemini)

REGRA: vozes de PERSONAGENS sempre Gemini. Só o NARRADOR (dublador) usa ElevenLabs.

Chaves em secrets/elevenlabs_keys.json: [{"id":1,"token":"...","status":"ok","fila":0}]
Proxies em secrets/el_proxies.txt (ou secrets/proxies.txt). Sem proxy -> NÃO chama.
"""
import json
import os
import subprocess
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
KEYS_FILE = PROJECT_DIR / "secrets" / "elevenlabs_keys.json"
PROXY_FILES = [PROJECT_DIR / "secrets" / "el_proxies.txt",
               PROJECT_DIR / "secrets" / "proxies.txt"]

API = "https://api.elevenlabs.io/v1"
MODEL = os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")
# Exige proxy por padrão (regra do usuário). Só desliga explicitamente em teste.
REQUIRE_PROXY = os.environ.get("ELEVENLABS_REQUIRE_PROXY", "1") == "1"

_keys = None
_key_idx = 0
_proxies = None
_dead_proxies = set()  # proxies que falharam nesta sessão (failover)
_credits_cache = {}  # token -> (restantes, ts)


def log(msg):
    import sys
    print(f"[EL] {msg}", file=sys.stderr)


# ─── Chaves ───────────────────────────────────────────────────────────────────
def _load_keys():
    global _keys
    if KEYS_FILE.exists():
        try:
            _keys = json.loads(KEYS_FILE.read_text())
        except Exception:
            _keys = []
    else:
        _keys = []
    return _keys


def _save_keys():
    if _keys is not None:
        KEYS_FILE.write_text(json.dumps(_keys, indent=2))


def _load_proxies():
    global _proxies
    _proxies = []
    for pf in PROXY_FILES:
        if pf.exists():
            for line in pf.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    _proxies.append(line)
            if _proxies:
                break
    return _proxies


def _get_working_proxy():
    """Retorna o 1º proxy vivo na ordem de prioridade (socks5 -> webshare).
    Pula os marcados como mortos nesta sessão (failover)."""
    if _proxies is None:
        _load_proxies()
    for p in (_proxies or []):
        if p not in _dead_proxies:
            return p
    return None


def _mark_proxy_dead(p):
    if p:
        _dead_proxies.add(p)
        log(f"  proxy morto nesta sessão: {p.split('@')[-1]}")


# ─── Créditos ─────────────────────────────────────────────────────────────────
def check_credits(token, proxy=None, force=False):
    """Retorna caracteres restantes da chave (cacheado 5min). None se falhar."""
    cached = _credits_cache.get(token)
    if cached and not force and time.time() - cached[1] < 300:
        return cached[0]
    cmd = ["curl", "-s", "-m", "20"]
    if proxy:
        cmd += ["-x", proxy]
    cmd += ["-H", f"xi-api-key: {token}", f"{API}/user/subscription"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        d = json.loads(r.stdout)
        remaining = int(d.get("character_limit", 0)) - int(d.get("character_count", 0))
        _credits_cache[token] = (remaining, time.time())
        return remaining
    except Exception:
        return None


def sync_all_credits():
    """Atualiza créditos de todas as chaves (pra dashboard/gestão)."""
    if _keys is None:
        _load_keys()
    out = []
    for k in (_keys or []):
        proxy = _get_working_proxy()
        rem = check_credits(k["token"], proxy=proxy, force=True)
        if rem is None and proxy:
            _mark_proxy_dead(proxy)
            rem = check_credits(k["token"], proxy=_get_working_proxy(), force=True)
        k["creditos_restantes"] = rem
        out.append({"id": k.get("id"), "restantes": rem})
    _save_keys()
    return out


def pick_key(min_chars=300):
    """Escolhe a próxima chave com crédito suficiente (round-robin). (id, token) ou (None,None)."""
    global _key_idx
    if _keys is None:
        _load_keys()
    keys = [k for k in (_keys or []) if k.get("status") != "expired"]
    if not keys:
        return (None, None)
    n = len(keys)
    for off in range(n):
        k = keys[(_key_idx + off) % n]
        proxy = _get_working_proxy() if (REQUIRE_PROXY or _proxies) else None
        rem = check_credits(k["token"], proxy=proxy)
        if rem is None and proxy:
            # proxy pode estar morto -> marca e tenta o próximo vivo
            _mark_proxy_dead(proxy)
            rem = check_credits(k["token"], proxy=_get_working_proxy())
        if rem is None:
            continue
        if rem >= min_chars:
            _key_idx = (_key_idx + off + 1) % n
            return (k.get("id"), k["token"])
        else:
            k["status"] = "sem_credito"
    return (None, None)


def list_voices(token, proxy=None):
    """Lista vozes disponíveis pra chave (premade + library se paga)."""
    cmd = ["curl", "-s", "-m", "20"]
    if proxy:
        cmd += ["-x", proxy]
    cmd += ["-H", f"xi-api-key: {token}", f"{API}/voices"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        return json.loads(r.stdout).get("voices", [])
    except Exception:
        return []


# ─── TTS ──────────────────────────────────────────────────────────────────────
def speak(text, voice_id, out_path, model=None, max_attempts=4,
          stability=0.45, similarity=0.8, style=0.35):
    """Sintetiza `text` com a `voice_id` da ElevenLabs (rotação de chave + proxy).

    Retorna True/False. False -> o caller deve usar Gemini como fallback.
    PROXY OBRIGATÓRIO se ELEVENLABS_REQUIRE_PROXY=1 (default).
    """
    text = (text or "").strip()
    if len(text) < 2:
        return False
    model = model or MODEL
    body = json.dumps({
        "text": text, "model_id": model,
        "voice_settings": {"stability": stability, "similarity_boost": similarity, "style": style},
    })

    for attempt in range(max_attempts):
        proxy = _get_working_proxy()
        if REQUIRE_PROXY and not proxy:
            log("[X] sem proxy de IP vivo e REQUIRE_PROXY=1 -> abortando (caller usa Gemini)")
            return False
        kid, token = pick_key(min_chars=len(text) + 50)
        if not token:
            log("[X] sem chave EL com crédito -> fallback Gemini")
            return False

        cmd = ["curl", "-s", "-m", "120", "-w", "\n%{http_code}"]
        if proxy:
            cmd += ["-x", proxy]
        cmd += ["-X", "POST", f"{API}/text-to-speech/{voice_id}",
                "-H", f"xi-api-key: {token}", "-H", "Content-Type: application/json",
                "-d", body, "--output", "-"]
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=130)
            raw = r.stdout
            # últimos 3 bytes = http_code (após \n)
            tail = raw.rsplit(b"\n", 1)
            code = tail[1].decode().strip() if len(tail) == 2 else "000"
            audio = tail[0]
            if code == "200" and len(audio) > 1000:
                Path(out_path).write_bytes(audio)
                # debita crédito do cache
                if token in _credits_cache:
                    rem, ts = _credits_cache[token]
                    _credits_cache[token] = (rem - len(text), ts)
                log(f"[OK] voz EL ok (key {kid}, voice {voice_id[:8]}, {len(audio)//1024}KB)")
                return True
            elif code in ("401", "402"):
                log(f"  key {kid}: HTTP {code} (sem permissão/plano) — marcando")
                for k in (_keys or []):
                    if k.get("token") == token:
                        k["status"] = "sem_permissao_voice"
                _save_keys()
            elif code == "429":
                log(f"  key {kid}: 429 rate limit, girando proxy/chave...")
                time.sleep(2 * (attempt + 1))
            elif code == "000":
                # falha de conexão = proxy morto -> marca e tenta o próximo
                _mark_proxy_dead(proxy)
            else:
                log(f"  key {kid}: HTTP {code}, retry...")
                time.sleep(1)
        except Exception as e:
            log(f"  erro curl: {str(e)[:80]}")
            _mark_proxy_dead(proxy)
            time.sleep(1)
    return False


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--credits", action="store_true", help="Mostra créditos de todas as chaves")
    ap.add_argument("--text", help="Texto pra testar TTS")
    ap.add_argument("--voice", default="pNInz6obpgDQGcFmaJgB", help="voice_id (default Adam)")
    ap.add_argument("--out", default="/tmp/el_test.mp3")
    ap.add_argument("--no-proxy", action="store_true", help="teste sem proxy (NÃO usar em produção)")
    a = ap.parse_args()
    if a.no_proxy:
        REQUIRE_PROXY = False
    if a.credits:
        print(json.dumps(sync_all_credits(), indent=2))
    if a.text:
        ok = speak(a.text, a.voice, a.out)
        print("OK" if ok else "FALHOU", "->", a.out if ok else "(fallback Gemini)")
