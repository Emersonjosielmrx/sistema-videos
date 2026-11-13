# -*- coding: utf-8 -*-
"""elevenlabs_veo: TTS ElevenLabs pro CTA da pos-producao do veo.

Reaproveita as 6 chaves free de D:\\postador-de-videos\\secrets\\elevenlabs_keys.json
(rotaciona quando uma esgota). Voz multilingual_v2 fala PT-BR nativo.

Uso:
    from elevenlabs_veo import speak, VOZES_CTA
    ok = speak("Fale comigo no WhatsApp...", out_wav="cta.wav", voz="sarah")

O CTA e FIXO por produto, entao o caller deve CACHEAR o wav — assim gastamos
~6 chamadas no total (uma por produto), nao uma por video. A cota free
(10k chars/mes x 6 chaves) fica folgada.
"""
import json
import os
import time
import urllib.request
import urllib.error
import subprocess
from pathlib import Path

# Chaves ficam no postador (fonte unica). Override por env ELEVENLABS_KEYS_JSON.
_KEYS_FILE = Path(os.environ.get(
    "ELEVENLABS_KEYS_JSON",
    r"D:\postador-de-videos\secrets\elevenlabs_keys.json"))
_FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"

# Vozes candidatas pro CTA (premade — funcionam no free; multilingual fala PT-BR).
VOZES_CTA = {
    "sarah":   {"id": "EXAVITQu4vr4xnSDxMaL", "desc": "feminina, madura, confiante (profissional)"},
    "bella":   {"id": "hpp4J3VqNfWAUOO0d1Us", "desc": "feminina, brilhante, calorosa"},
    "matilda": {"id": "XrExE9yKIg1WjnnlVkGX", "desc": "feminina, animada, profissional"},
    "adam":    {"id": "pNInz6obpgDQGcFmaJgB", "desc": "masculina, firme, dominante (vendedor)"},
    "eric":    {"id": "cjVigY5qzO86Huf0OWal", "desc": "masculina, suave, confiavel"},
}
VOZ_PADRAO = os.environ.get("ELEVENLABS_VOZ", "sarah")

_keys_data = None
_key_idx = 0


def _log(msg):
    print(f"[elevenlabs_veo] {msg}", flush=True)


def _load_keys():
    global _keys_data
    if _keys_data is None:
        try:
            _keys_data = json.loads(_KEYS_FILE.read_text(encoding="utf-8"))
        except Exception:
            _keys_data = {"keys": []}
    return _keys_data


def _save_keys():
    if _keys_data:
        try:
            _KEYS_FILE.write_text(
                json.dumps(_keys_data, indent=2, ensure_ascii=False),
                encoding="utf-8")
        except Exception:
            pass


def _next_key():
    global _key_idx
    keys = _load_keys().get("keys", [])
    for _ in range(len(keys)):
        k = keys[_key_idx % len(keys)]
        _key_idx += 1
        if k.get("status") == "available":
            return k
    return None


def _mark_exhausted(k):
    k["status"] = "exhausted"
    k["used_at"] = time.strftime("%Y-%m-%d")
    _save_keys()
    _log(f"chave '{k.get('name')}' esgotou creditos do mes")


def disponivel() -> bool:
    """True se ha alguma chave ElevenLabs available."""
    return any(k.get("status") == "available"
               for k in _load_keys().get("keys", []))


def speak(text: str, out_wav, voz: str = None) -> bool:
    """Gera TTS ElevenLabs em out_wav (WAV 44.1k). True se sucesso.

    Rotaciona chaves em 401/429/quota. Retorna False se todas esgotaram
    (caller cai no Edge-TTS).
    """
    text = (text or "").strip()
    if len(text) < 4:
        return False
    out_wav = Path(out_wav)
    voz = (voz or VOZ_PADRAO).lower()
    vid = VOZES_CTA.get(voz, VOZES_CTA["sarah"])["id"]

    tmp_mp3 = out_wav.with_suffix(".tmp.mp3")
    for _ in range(len(_load_keys().get("keys", [])) or 1):
        k = _next_key()
        if not k:
            _log("todas as chaves esgotadas este mes")
            return False
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{vid}"
            body = json.dumps({
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.8,
                    "style": 0.35,
                    "use_speaker_boost": True,
                },
            }).encode()
            req = urllib.request.Request(
                url, data=body,
                headers={"xi-api-key": k["token"],
                         "Content-Type": "application/json",
                         "Accept": "audio/mpeg"},
                method="POST")
            with urllib.request.urlopen(req, timeout=45) as resp:
                mp3 = resp.read()
            if len(mp3) < 500:
                _log(f"resposta pequena ({len(mp3)}B), proxima chave")
                continue
            tmp_mp3.write_bytes(mp3)
            subprocess.run(
                [_FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                 "-i", str(tmp_mp3), "-ar", "44100", "-ac", "2", str(out_wav)],
                check=True, capture_output=True, timeout=30)
            tmp_mp3.unlink(missing_ok=True)
            if out_wav.exists() and out_wav.stat().st_size > 1000:
                _log(f"OK {out_wav.name} ({out_wav.stat().st_size//1024}KB) voz={voz} key={k.get('name')}")
                return True
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "replace")[:150]
            if e.code in (401, 429) or "quota" in msg.lower() or "limit" in msg.lower():
                _mark_exhausted(k)
                continue
            _log(f"HTTP {e.code}: {msg}")
            return False
        except Exception as e:
            _log(f"erro: {str(e)[:100]}")
            tmp_mp3.unlink(missing_ok=True)
            return False
    return False


if __name__ == "__main__":
    # Gera amostras de todas as vozes candidatas pra escolha
    import sys
    texto = (sys.argv[1] if len(sys.argv) > 1 else
             "Atenda, ligue e venda pelo WhatsApp sem parar. "
             "Hermes Call faz ligacoes automaticas com inteligencia artificial. "
             "Fale comigo no WhatsApp 91 9 8469 8653.")
    outdir = Path(__file__).resolve().parent / "tmp" / "amostras_voz"
    outdir.mkdir(parents=True, exist_ok=True)
    print(f"disponivel: {disponivel()}")
    for nome in VOZES_CTA:
        wav = outdir / f"amostra_{nome}.wav"
        ok = speak(texto, wav, voz=nome)
        print(f"  {nome:9} {'OK' if ok else 'FALHOU'} -> {wav}")
