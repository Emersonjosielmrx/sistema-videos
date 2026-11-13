"""test_all_voices.py — Gera o MESMO texto com TODAS as vozes disponíveis pra comparação.

Engines testadas:
1. Edge-TTS (18 virtual voices + narrador)
2. ElevenLabs (13 vozes masculinas)
3. OmniRoute GPT Audio (1 voz)

Saída: D:\hipercool-inferior-fix\workspace\_voice_tests\
"""
import asyncio
import sys
import os
import json
import time
import base64
import subprocess
import urllib.request
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT_DIR / "workspace" / "_voice_tests"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TEXTO = (
    "Ele nunca imaginou que aquele seria seu último dia. "
    "O sangue escorria pelo chão enquanto a escuridão tomava conta de tudo. "
    "Mas no fundo do seu coração, uma chama ainda ardia."
)

VIRTUAL_VOICES = {
    "francisca_normal":  {"voice": "pt-BR-FranciscaNeural", "rate": "+0%",  "pitch": "+0Hz"},
    "francisca_aguda":   {"voice": "pt-BR-FranciscaNeural", "rate": "+0%",  "pitch": "+8Hz"},
    "francisca_grave":   {"voice": "pt-BR-FranciscaNeural", "rate": "+0%",  "pitch": "-5Hz"},
    "francisca_rapida":  {"voice": "pt-BR-FranciscaNeural", "rate": "+15%", "pitch": "+3Hz"},
    "francisca_lenta":   {"voice": "pt-BR-FranciscaNeural", "rate": "-10%", "pitch": "-3Hz"},
    "francisca_sussurro":{"voice": "pt-BR-FranciscaNeural", "rate": "-5%",  "pitch": "+10Hz"},
    "francisca_animada": {"voice": "pt-BR-FranciscaNeural", "rate": "+20%", "pitch": "+6Hz"},
    "thalita_normal":    {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "+0%",  "pitch": "+0Hz"},
    "thalita_aguda":     {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "+5%",  "pitch": "+8Hz"},
    "thalita_grave":     {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "+0%",  "pitch": "-5Hz"},
    "thalita_rapida":    {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "+15%", "pitch": "+0Hz"},
    "thalita_madura":    {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "-8%",  "pitch": "-8Hz"},
    "thalita_doce":      {"voice": "pt-BR-ThalitaMultilingualNeural", "rate": "-3%",  "pitch": "+12Hz"},
    "antonio_acelerado": {"voice": "pt-BR-AntonioNeural", "rate": "+20%", "pitch": "+3Hz"},
    "antonio_grave":     {"voice": "pt-BR-AntonioNeural", "rate": "+10%", "pitch": "-5Hz"},
    "antonio_agudo":     {"voice": "pt-BR-AntonioNeural", "rate": "+15%", "pitch": "+8Hz"},
    "antonio_jovem":     {"voice": "pt-BR-AntonioNeural", "rate": "+25%", "pitch": "+10Hz"},
    "antonio_meio":      {"voice": "pt-BR-AntonioNeural", "rate": "+15%", "pitch": "+0Hz"},
    "antonio_lento":     {"voice": "pt-BR-AntonioNeural", "rate": "-5%",  "pitch": "-8Hz"},
}
NARRATOR_PROFILE = {"voice": "pt-BR-FranciscaNeural", "rate": "+5%", "pitch": "+0Hz"}

ELEVENLABS_VOICES = [
    {"name": "Brian", "id": "nPczCjzI2devNBz1zQrb", "style": "deep resonant"},
    {"name": "Adam", "id": "pNInz6obpgDQGcFmaJgB", "style": "dominant firm"},
    {"name": "Eric", "id": "cjVigY5qzO86Huf0OWal", "style": "smooth trustworthy"},
    {"name": "Chris", "id": "iP95p4xoKVk53GoZ742B", "style": "charming"},
    {"name": "George", "id": "JBFqnCBsd6RMkjVDRZzb", "style": "warm storyteller"},
    {"name": "Charlie", "id": "IKne3meq5aSn9XLyUdCD", "style": "deep confident"},
    {"name": "Roger", "id": "CwhRBWXzGAHq8TQ4Fs17", "style": "laid-back casual"},
    {"name": "Daniel", "id": "onwK4e9ZLuTAKqWW03F9", "style": "steady broadcaster"},
    {"name": "Liam", "id": "TX3LPaxmHKxFdv7VOQHJ", "style": "energetic"},
    {"name": "Bill", "id": "pqHfZKP75CvOlQylNhV4", "style": "wise mature"},
    {"name": "Harry", "id": "SOYHLrjzK2X1ezoPC6cr", "style": "fierce warrior"},
    {"name": "Callum", "id": "N2lVS1w4EtoT3dr4eOWO", "style": "husky trickster"},
    {"name": "Will", "id": "bIHbv24MWmeRgasZH58o", "style": "relaxed optimist"},
]

OMNIROUTE_URL = "http://157.173.207.22:20128/v1/chat/completions"
OMNIROUTE_KEY = "Bearer <SEGREDO_REMOVIDO>"


def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


# ─── Edge-TTS ───────────────────────────────────────────────────────
async def gen_edge_tts(name, profile, out_path):
    try:
        import edge_tts
        comm = edge_tts.Communicate(
            TEXTO,
            voice=profile["voice"],
            rate=profile["rate"],
            pitch=profile["pitch"],
        )
        await comm.save(str(out_path))
        if out_path.exists() and out_path.stat().st_size > 1000:
            log(f"  OK edge-tts/{name} ({out_path.stat().st_size // 1024} KB)")
            return True
    except Exception as e:
        log(f"  FALHOU edge-tts/{name}: {e}")
    return False


async def run_edge_tts():
    log("=== EDGE-TTS (19 vozes) ===")
    edge_dir = OUT_DIR / "01_edge_tts"
    edge_dir.mkdir(exist_ok=True)

    results = []

    # Narrador
    out = edge_dir / "00_narrador.mp3"
    ok = await gen_edge_tts("narrador", NARRATOR_PROFILE, out)
    results.append(("narrador", "Francisca +5% rate", ok, out))

    # Todas as virtual voices
    for i, (name, profile) in enumerate(VIRTUAL_VOICES.items(), 1):
        out = edge_dir / f"{i:02d}_{name}.mp3"
        ok = await gen_edge_tts(name, profile, out)
        base = profile["voice"].split("-")[-1].replace("Neural", "")
        desc = f"{base} rate={profile['rate']} pitch={profile['pitch']}"
        results.append((name, desc, ok, out))

    return results


# ─── ElevenLabs ─────────────────────────────────────────────────────
def gen_elevenlabs(voice_info, out_path, api_key):
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_info['id']}"
        body = json.dumps({
            "text": TEXTO,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }).encode()

        req = urllib.request.Request(url, data=body, headers={
            "Content-Type": "application/json",
            "xi-api-key": api_key,
        })
        resp = urllib.request.urlopen(req, timeout=30)
        audio = resp.read()
        if len(audio) > 1000:
            out_path.write_bytes(audio)
            log(f"  OK eleven/{voice_info['name']} ({len(audio) // 1024} KB)")
            return True
        else:
            log(f"  FALHOU eleven/{voice_info['name']}: audio muito pequeno")
    except Exception as e:
        log(f"  FALHOU eleven/{voice_info['name']}: {e}")
    return False


def run_elevenlabs():
    log("=== ELEVENLABS (13 vozes masculinas) ===")
    eleven_dir = OUT_DIR / "02_elevenlabs"
    eleven_dir.mkdir(exist_ok=True)

    keys_file = PROJECT_DIR / "secrets" / "elevenlabs_keys.json"
    if not keys_file.exists():
        log("  SKIP: secrets/elevenlabs_keys.json nao encontrado")
        return []

    keys_data = json.loads(keys_file.read_text(encoding="utf-8"))
    api_keys = keys_data.get("keys", [])
    if not api_keys:
        log("  SKIP: nenhuma key ElevenLabs")
        return []

    api_key = api_keys[0] if isinstance(api_keys[0], str) else api_keys[0].get("key", "")
    results = []

    for i, v in enumerate(ELEVENLABS_VOICES):
        out = eleven_dir / f"{i+1:02d}_{v['name'].lower()}.mp3"
        ok = gen_elevenlabs(v, out, api_key)
        results.append((v["name"], v["style"], ok, out))
        time.sleep(1)

    return results


# ─── OmniRoute GPT Audio ───────────────────────────────────────────
def gen_omniroute(out_path):
    try:
        prompt = (
            f"Leia o texto abaixo em portugues brasileiro com voz masculina, "
            f"tom natural e expressivo, como narracao de anime:\n\n{TEXTO}"
        )
        body = json.dumps({
            "model": "openrouter/openai/gpt-audio-mini",
            "messages": [{"role": "user", "content": prompt}],
            "modalities": ["audio"],
        }).encode()

        req = urllib.request.Request(OMNIROUTE_URL, data=body, headers={
            "Content-Type": "application/json",
            "Authorization": OMNIROUTE_KEY,
        })

        resp = urllib.request.urlopen(req, timeout=60)
        data = json.loads(resp.read())
        audio_b64 = data.get("choices", [{}])[0].get("message", {}).get("audio", {}).get("data")

        if not audio_b64:
            log("  FALHOU omniroute: sem campo audio na resposta")
            return False

        audio_bytes = base64.b64decode(audio_b64)
        if len(audio_bytes) < 500:
            log(f"  FALHOU omniroute: audio muito pequeno ({len(audio_bytes)})")
            return False

        tmp = out_path.with_suffix(".tmp")
        tmp.write_bytes(audio_bytes)
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(tmp), "-ar", "44100", "-ac", "2", str(out_path)],
            check=True, capture_output=True, timeout=30,
        )
        tmp.unlink(missing_ok=True)

        if out_path.exists() and out_path.stat().st_size > 1000:
            log(f"  OK omniroute/gpt-audio ({out_path.stat().st_size // 1024} KB)")
            return True
    except Exception as e:
        log(f"  FALHOU omniroute: {e}")
    return False


def run_omniroute():
    log("=== OMNIROUTE GPT AUDIO (1 voz) ===")
    omni_dir = OUT_DIR / "03_omniroute"
    omni_dir.mkdir(exist_ok=True)
    out = omni_dir / "01_gpt_audio_mini.wav"
    ok = gen_omniroute(out)
    return [("GPT Audio Mini", "voz IA masculina (OmniRoute)", ok, out)]


# ─── Main ───────────────────────────────────────────────────────────
async def main():
    log(f"Texto de teste ({len(TEXTO)} chars):")
    log(f"  \"{TEXTO}\"")
    log(f"Pasta de saida: {OUT_DIR}")
    log("")

    all_results = []

    # 1. Edge-TTS
    edge_results = await run_edge_tts()
    all_results.extend([("Edge-TTS", *r) for r in edge_results])

    # 2. ElevenLabs
    eleven_results = run_elevenlabs()
    all_results.extend([("ElevenLabs", *r) for r in eleven_results])

    # 3. OmniRoute
    omni_results = run_omniroute()
    all_results.extend([("OmniRoute", *r) for r in omni_results])

    # Resumo
    log("")
    log("=" * 70)
    log("RESUMO")
    log("=" * 70)
    ok_count = sum(1 for r in all_results if r[3])
    fail_count = sum(1 for r in all_results if not r[3])
    log(f"Total: {len(all_results)} vozes | OK: {ok_count} | Falhou: {fail_count}")
    log("")

    log(f"{'Engine':<12} {'Voz':<25} {'Estilo':<30} {'Status':<6} {'Arquivo'}")
    log("-" * 110)
    for engine, name, style, ok, path in all_results:
        status = "OK" if ok else "FALHOU"
        fname = path.name if ok else "-"
        log(f"{engine:<12} {name:<25} {style:<30} {status:<6} {fname}")

    log("")
    log(f"Arquivos em: {OUT_DIR}")
    log("Abra a pasta e escute cada um pra comparar!")


if __name__ == "__main__":
    asyncio.run(main())
