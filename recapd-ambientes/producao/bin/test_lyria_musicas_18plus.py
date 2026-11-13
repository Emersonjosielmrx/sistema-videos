"""test_lyria_musicas_18plus.py — Trilhas temáticas pra manhwa +18/hentai.

Estilos: sensual, dark seduction, provocante, ecchi comedy, tensão sexual,
romance proibido, etc. Nada de shounen genérico — é conteúdo adulto.
"""
import json
import base64
import time
import subprocess
import http.client
import urllib.parse
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT_DIR / "workspace" / "_voice_tests" / "12_trilhas_18plus"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OMNIROUTE_URL = "http://157.173.207.22:20128/v1/chat/completions"
OMNIROUTE_KEY = "Bearer <SEGREDO_REMOVIDO>"

TRILHAS = [
    # --- SENSUAIS / SEDUÇÃO ---
    ("01_dark_seduction_pro", "openrouter/google/lyria-3-pro-preview",
     "Compose dark seductive music, slow sensual bass, breathy atmosphere, "
     "mysterious and alluring, like a forbidden midnight encounter. "
     "Deep 808 sub-bass, sultry synth pads, slow grinding beat. 30 seconds."),

    ("02_dark_seduction_clip", "openrouter/google/lyria-3-clip-preview",
     "Compose dark seductive music, slow sensual bass, breathy atmosphere, "
     "mysterious and alluring, forbidden midnight encounter vibe. 15 seconds."),

    ("03_sensual_rnb_pro", "openrouter/google/lyria-3-pro-preview",
     "Compose smooth sensual R&B instrumental, slow tempo, sexy groove, "
     "warm bass, intimate atmosphere, bedroom vibes, late night mood. "
     "No vocals, just pure seductive instrumental. 30 seconds."),

    ("04_sensual_rnb_clip", "openrouter/google/lyria-3-clip-preview",
     "Compose smooth sensual R&B instrumental, slow tempo, sexy groove, "
     "warm bass, intimate bedroom vibes, late night mood. 15 seconds."),

    # --- TENSÃO SEXUAL / PROVOCANTE ---
    ("05_tension_buildup_pro", "openrouter/google/lyria-3-pro-preview",
     "Compose music with building sexual tension, starting soft and innocent "
     "then gradually becoming more intense and provocative. Pulsing synths, "
     "heartbeat-like bass, rising anticipation, dramatic climax. 30 seconds."),

    ("06_tension_buildup_clip", "openrouter/google/lyria-3-clip-preview",
     "Compose music with building tension, starting soft then becoming intense "
     "and provocative. Pulsing synths, heartbeat bass, rising anticipation. 15 seconds."),

    ("07_forbidden_romance_pro", "openrouter/google/lyria-3-pro-preview",
     "Compose bittersweet forbidden romance music, piano and strings, "
     "passionate but melancholic, like a secret love affair that shouldn't exist. "
     "Beautiful melody with underlying sadness and desire. 30 seconds."),

    ("08_forbidden_romance_clip", "openrouter/google/lyria-3-clip-preview",
     "Compose forbidden romance music, piano and strings, passionate but melancholic, "
     "secret love affair vibe, beautiful melody with desire. 15 seconds."),

    # --- ECCHI COMEDY ---
    ("09_ecchi_comedy_pro", "openrouter/google/lyria-3-pro-preview",
     "Compose playful naughty comedy music, cheeky and mischievous, "
     "like an ecchi anime scene where something embarrassing happens. "
     "Bouncy bass, comedic timing, wink-wink vibes, funky and fun. 30 seconds."),

    ("10_ecchi_comedy_clip", "openrouter/google/lyria-3-clip-preview",
     "Compose playful naughty comedy music, cheeky and mischievous, "
     "ecchi anime vibe, bouncy and funky with comedic timing. 15 seconds."),

    # --- DARK / DOMINAÇÃO ---
    ("11_dark_domination_pro", "openrouter/google/lyria-3-pro-preview",
     "Compose dark dominant music, heavy industrial bass, aggressive and controlling, "
     "power dynamics atmosphere, ominous synths, commanding presence, "
     "like a dark manhwa villain asserting total control. 30 seconds."),

    ("12_dark_domination_clip", "openrouter/google/lyria-3-clip-preview",
     "Compose dark dominant music, heavy industrial bass, aggressive, "
     "power dynamics, ominous synths, commanding dark villain vibe. 15 seconds."),

    # --- HIPNOSE / PSICODÉLICO ---
    ("13_hypnotic_trance_pro", "openrouter/google/lyria-3-pro-preview",
     "Compose hypnotic trance music, swirling psychedelic synths, "
     "mind-control atmosphere, pulsing and mesmerizing, deep reverb, "
     "like falling under a spell, dreamy and disorienting. 30 seconds."),

    ("14_hypnotic_trance_clip", "openrouter/google/lyria-3-clip-preview",
     "Compose hypnotic trance music, swirling synths, mind-control atmosphere, "
     "pulsing, mesmerizing, falling under a spell. 15 seconds."),

    # --- NOITE / CLUB ---
    ("15_midnight_club_pro", "openrouter/google/lyria-3-pro-preview",
     "Compose late night club music, deep house vibes, sensual and dark, "
     "4-on-the-floor beat, warm pads, seductive atmosphere, "
     "like 3AM in a dimly lit nightclub. 30 seconds."),

    ("16_midnight_club_clip", "openrouter/google/lyria-3-clip-preview",
     "Compose late night club music, deep house, sensual and dark, "
     "seductive 3AM nightclub atmosphere. 15 seconds."),

    # --- ROMANCE INTENSO ---
    ("17_passionate_climax_pro", "openrouter/google/lyria-3-pro-preview",
     "Compose intensely passionate orchestral music, building from tender to explosive, "
     "sweeping strings, powerful crescendo, overwhelming emotion, "
     "like the climactic emotional moment in a romance drama. 30 seconds."),

    ("18_passionate_climax_clip", "openrouter/google/lyria-3-clip-preview",
     "Compose passionate orchestral music, tender building to explosive, "
     "sweeping strings, powerful crescendo, romance drama climax. 15 seconds."),

    # --- TRAP SENSUAL ---
    ("19_trap_sensual_pro", "openrouter/google/lyria-3-pro-preview",
     "Compose sensual trap beat, slow 808 bass, moody hi-hats, "
     "dark and sexy atmosphere, modern urban nightlife vibes, "
     "confident and seductive, like a manhwa playboy character. 30 seconds."),

    ("20_trap_sensual_clip", "openrouter/google/lyria-3-clip-preview",
     "Compose sensual trap beat, slow 808, moody hi-hats, dark sexy atmosphere, "
     "manhwa playboy character vibes. 15 seconds."),
]


def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def call_omniroute(prompt, model, out_path, timeout=300):
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
            except Exception:
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

        subprocess.run(
            ["ffmpeg", "-y", "-i", str(tmp), "-ar", "44100", "-ac", "2", "-b:a", "192k", str(out_path)],
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
    log("LYRIA — TRILHAS TEMATICAS MANHWA +18 / HENTAI")
    log("=" * 60)
    log(f"20 trilhas (10 PRO + 10 CLIP), destino: {OUT_DIR}")
    log("")

    ok_count = 0
    fail_streak = 0

    for nome, model, prompt in TRILHAS:
        tag = "PRO" if "pro" in model else "CLIP"
        out = OUT_DIR / f"{nome}.mp3"

        if out.exists() and out.stat().st_size > 1000:
            log(f"  [{nome}] ({tag}) ja existe, pulando")
            ok_count += 1
            fail_streak = 0
            continue

        log(f"  [{nome}] ({tag}) gerando...")
        ok = call_omniroute(prompt, model, out)
        if ok:
            kb = out.stat().st_size // 1024
            log(f"    OK ({kb} KB)")
            ok_count += 1
            fail_streak = 0
        else:
            log(f"    FALHOU")
            fail_streak += 1
            if fail_streak >= 3:
                log("  3+ falhas seguidas — proxy fora. Parando pra nao gastar tempo.")
                break
        time.sleep(3)

    log("")
    log("=" * 60)
    log(f"=== {ok_count}/{len(TRILHAS)} geradas ===")
    log(f"Pasta: {OUT_DIR}")
    log("")
    log("Categorias:")
    log("  01-04: Sensual / Dark Seduction / R&B")
    log("  05-08: Tensao Sexual / Romance Proibido")
    log("  09-10: Ecchi Comedy")
    log("  11-12: Dark Dominacao")
    log("  13-14: Hipnose / Trance")
    log("  15-16: Midnight Club")
    log("  17-18: Romance Intenso / Climax")
    log("  19-20: Trap Sensual")


if __name__ == "__main__":
    main()
