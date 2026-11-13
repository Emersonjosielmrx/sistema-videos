"""test_omniroute_complete.py — Completa os testes que faltaram (Premium 14-18 + Lyria Pro/Clip)."""
import json
import base64
import time
import subprocess
import http.client
import urllib.parse
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT_DIR / "workspace" / "_voice_tests"

OMNIROUTE_URL = "http://157.173.207.22:20128/v1/chat/completions"
OMNIROUTE_KEY = "Bearer <SEGREDO_REMOVIDO>"

TEXTO = (
    "Ele nunca imaginou que aquele seria seu ultimo dia. "
    "O sangue escorria pelo chao enquanto a escuridao tomava conta de tudo. "
    "Mas no fundo do seu coracao, uma chama ainda ardia."
)

PREMIUM_FALTANDO = [
    ("14_fem_terror",   "Feminina terror",
     "Voce e uma narradora FEMININA de TERROR. Leia em tom assustador, voz baixa e tensa, com pausas que criam suspense:"),
    ("15_audiobook",    "Audiobook profissional",
     "Voce e um narrador profissional de AUDIOBOOK. Leia com clareza perfeita, ritmo controlado, tom neutro mas envolvente:"),
    ("16_podcast",      "Podcast conversacional",
     "Voce e um host de PODCAST. Leia de forma CONVERSACIONAL e natural, como se estivesse falando com um amigo, tom casual:"),
    ("17_trailer",      "Trailer de filme",
     "Voce e o narrador de um TRAILER DE FILME EPICO. Voz grave, dramatica, com pausas cinematograficas. Tipo 'In a world where...':"),
    ("18_esportivo",    "Narrador esportivo",
     "Voce e um NARRADOR ESPORTIVO empolgado. Leia como se fosse um gol decisivo, com crescentes de emocao e explosoes de entusiasmo:"),
]

MUSICA_ESTILOS = [
    ("01_epic_battle",   "Epica de batalha",
     "Compose an epic anime battle soundtrack with Japanese taiko drums, dramatic orchestral strings, and rising intensity. 30 seconds."),
    ("02_sad_emotional", "Triste emocional",
     "Compose a melancholic emotional piano piece with soft strings, bittersweet and moving, like a sad anime scene. 30 seconds."),
    ("03_dark_tension",  "Dark suspense",
     "Compose dark suspenseful music with ominous low strings, eerie atmosphere, building dread, psychological thriller style. 30 seconds."),
    ("04_comedy_fun",    "Comedia leve",
     "Compose light playful music for a comedic anime scene, quirky instruments, bouncy rhythm, slice-of-life style. 30 seconds."),
    ("05_romantic",      "Romantica",
     "Compose romantic atmospheric music with gentle piano and warm strings, intimate and tender mood. 30 seconds."),
]


def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def call_omniroute(prompt, model, out_path, ext="wav", timeout=180):
    try:
        body = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "modalities": ["audio"],
            "stream": True,
        }).encode()

        parsed = urllib.parse.urlparse(OMNIROUTE_URL)
        conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=timeout)
        conn.request("POST", parsed.path, body=body, headers={
            "Content-Type": "application/json",
            "Authorization": OMNIROUTE_KEY,
        })
        resp = conn.getresponse()

        if resp.status != 200:
            err = resp.read().decode(errors="replace")
            log(f"    HTTP {resp.status}: {err[:200]}")
            conn.close()
            return False

        raw = resp.read().decode(errors="replace")
        conn.close()

        audio_chunks = []
        for line in raw.split("\n"):
            line = line.strip()
            if not line.startswith("data: "):
                continue
            payload = line[6:]
            if payload == "[DONE]":
                break
            try:
                chunk = json.loads(payload)
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                audio_data = delta.get("audio", {})
                if isinstance(audio_data, dict) and audio_data.get("data"):
                    audio_chunks.append(audio_data["data"])
            except json.JSONDecodeError:
                pass

        if not audio_chunks:
            try:
                data = json.loads(raw)
                b64 = data.get("choices", [{}])[0].get("message", {}).get("audio", {}).get("data")
                if b64:
                    audio_chunks = [b64]
            except:
                pass

        if not audio_chunks:
            log(f"    Sem audio (resp: {raw[:150]})")
            return False

        full_b64 = "".join(audio_chunks)
        audio_bytes = base64.b64decode(full_b64)

        if len(audio_bytes) < 500:
            log(f"    Audio muito pequeno ({len(audio_bytes)} bytes)")
            return False

        tmp = out_path.with_suffix(".tmp")
        tmp.write_bytes(audio_bytes)

        if ext == "mp3":
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(tmp), "-ar", "44100", "-ac", "2", "-b:a", "192k", str(out_path)],
                check=True, capture_output=True, timeout=30,
            )
        else:
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(tmp), "-ar", "44100", "-ac", "2", str(out_path)],
                check=True, capture_output=True, timeout=30,
            )
        tmp.unlink(missing_ok=True)

        if out_path.exists() and out_path.stat().st_size > 1000:
            return True
    except Exception as e:
        log(f"    Erro: {e}")
    return False


def main():
    log("=" * 60)
    log("COMPLETANDO TESTES OMNIROUTE (faltantes)")
    log("=" * 60)

    # --- Premium faltando (5 vozes) ---
    log("")
    log(">>> GPT AUDIO PREMIUM — 5 vozes faltantes")
    premium_dir = OUT_DIR / "05_gpt_audio_premium"
    premium_dir.mkdir(parents=True, exist_ok=True)
    premium_ok = 0
    for nome, desc, prompt in PREMIUM_FALTANDO:
        out = premium_dir / f"{nome}.wav"
        if out.exists() and out.stat().st_size > 1000:
            log(f"  [{nome}] ja existe, pulando")
            premium_ok += 1
            continue
        log(f"  [{nome}] {desc}")
        full_prompt = prompt + "\n\n" + TEXTO
        ok = call_omniroute(full_prompt, "openrouter/openai/gpt-audio", out, timeout=180)
        if ok:
            kb = out.stat().st_size // 1024
            log(f"    OK ({kb} KB)")
            premium_ok += 1
        else:
            log(f"    FALHOU")
        time.sleep(2)
    log(f"  Premium faltantes: {premium_ok}/{len(PREMIUM_FALTANDO)}")

    # --- Lyria Pro (5 musicas longas) ---
    log("")
    log(">>> LYRIA PRO (musica longa, GRATIS)")
    lyria_pro_dir = OUT_DIR / "06_lyria_pro"
    lyria_pro_dir.mkdir(parents=True, exist_ok=True)
    lyria_pro_ok = 0
    for nome, desc, prompt in MUSICA_ESTILOS:
        out = lyria_pro_dir / f"{nome}.mp3"
        if out.exists() and out.stat().st_size > 1000:
            log(f"  [{nome}] ja existe, pulando")
            lyria_pro_ok += 1
            continue
        log(f"  [{nome}] {desc}")
        ok = call_omniroute(prompt, "openrouter/google/lyria-3-pro-preview", out, ext="mp3", timeout=300)
        if ok:
            kb = out.stat().st_size // 1024
            log(f"    OK ({kb} KB)")
            lyria_pro_ok += 1
        else:
            log(f"    FALHOU")
        time.sleep(3)
    log(f"  Lyria Pro: {lyria_pro_ok}/{len(MUSICA_ESTILOS)}")

    # --- Lyria Clip (5 musicas curtas) ---
    log("")
    log(">>> LYRIA CLIP (musica curta, GRATIS)")
    lyria_clip_dir = OUT_DIR / "07_lyria_clip"
    lyria_clip_dir.mkdir(parents=True, exist_ok=True)
    lyria_clip_ok = 0
    for nome, desc, prompt in MUSICA_ESTILOS:
        out = lyria_clip_dir / f"{nome}.mp3"
        if out.exists() and out.stat().st_size > 1000:
            log(f"  [{nome}] ja existe, pulando")
            lyria_clip_ok += 1
            continue
        log(f"  [{nome}] {desc}")
        ok = call_omniroute(prompt, "openrouter/google/lyria-3-clip-preview", out, ext="mp3", timeout=300)
        if ok:
            kb = out.stat().st_size // 1024
            log(f"    OK ({kb} KB)")
            lyria_clip_ok += 1
        else:
            log(f"    FALHOU")
        time.sleep(3)
    log(f"  Lyria Clip: {lyria_clip_ok}/{len(MUSICA_ESTILOS)}")

    # --- Contagem total final ---
    log("")
    log("=" * 60)
    log("RESUMO COMPLETO (todas as pastas)")
    log("=" * 60)

    for folder, label in [
        ("04_gpt_audio_mini", "GPT Audio Mini"),
        ("05_gpt_audio_premium", "GPT Audio Premium"),
        ("06_lyria_pro", "Lyria Pro"),
        ("07_lyria_clip", "Lyria Clip"),
    ]:
        d = OUT_DIR / folder
        count = len(list(d.glob("*.*"))) if d.exists() else 0
        log(f"  {label:25s}: {count} arquivos")

    log("")
    log("Abre workspace/_voice_tests/ pastas 04-07 e escuta!")


if __name__ == "__main__":
    main()
