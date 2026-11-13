"""test_lyria_openings_obras.py — Openings em PORTUGUES pra cada obra do hipercool, estilos variados."""
import json
import base64
import time
import subprocess
import http.client
import urllib.parse
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT_DIR / "workspace" / "_voice_tests" / "10_openings_obras_ptbr"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OMNIROUTE_URL = "http://157.173.207.22:20128/v1/chat/completions"
OMNIROUTE_KEY = "Bearer <SEGREDO_REMOVIDO>"

OBRAS = [
    ("01_regressed_warriors", "Regressed Warriors",
     "Compose an epic anime opening song with male vocals singing in Brazilian Portuguese about a warrior who goes back in time to fix his mistakes. Heavy rock with orchestral elements, aggressive drums, electric guitar riffs, shounen battle style. Powerful chorus about revenge and redemption. 30 seconds."),

    ("02_the_meek_cat", "The Meek Cat",
     "Compose a dark mysterious anime opening with female vocals singing in Brazilian Portuguese about a seemingly weak person hiding immense power. Start soft and mysterious, then explode into heavy drums. Mix of electronic beats and orchestral, thriller vibe. 30 seconds."),

    ("03_the_cheat_hitter", "The Cheat Hitter",
     "Compose a high-energy trap/hip-hop anime opening with male vocals rapping in Brazilian Portuguese about someone who cheats the system and dominates everyone. Heavy 808 bass, aggressive flow, confident and arrogant tone, modern manhwa style. 30 seconds."),

    ("04_wonderful_new_world", "Wonderful New World",
     "Compose a dramatic K-pop style anime opening with mixed male and female vocals singing in Brazilian Portuguese about discovering a new world full of temptation and danger. Synth-heavy, dramatic drops, sensual undertone, polished pop production. 30 seconds."),

    ("05_what_happens_dungeon", "What Happens Inside the Dungeon",
     "Compose a fantasy adventure anime opening with male vocals singing in Brazilian Portuguese about exploring dangerous dungeons. Epic orchestral with choir, building crescendo, heroic melody, RPG game style music with brass and strings. 30 seconds."),

    ("06_hero_manager", "Hero Manager",
     "Compose an upbeat motivational anime opening with male vocals singing in Brazilian Portuguese about managing heroes and building a team. Energetic pop-rock, catchy chorus, inspirational tone, slice-of-life meets action style. 30 seconds."),

    ("07_the_inheritor", "The Inheritor",
     "Compose a dark power metal anime opening with deep male vocals singing in Brazilian Portuguese about inheriting forbidden power. Heavy double bass drums, shredding guitars, epic choir in background, dark fantasy atmosphere. 30 seconds."),

    ("08_absolute_hypnosis", "Absolute Hypnosis Another World",
     "Compose a hypnotic psychedelic anime opening with ethereal vocals singing in Brazilian Portuguese about controlling minds in another world. Trippy synths, pulsing bass, dreamy reverb effects, mysterious and seductive atmosphere. 30 seconds."),

    ("09_tremors", "Tremors",
     "Compose an intense horror anime opening with distorted vocals singing in Brazilian Portuguese about earthquakes and underground terror. Industrial metal, heavy distortion, ominous low frequencies, earthquake sound design elements, terrifying buildup. 30 seconds."),

    ("10_taming_noona", "Taming Noona",
     "Compose a sexy R&B anime opening with smooth male vocals singing in Brazilian Portuguese about taming an older woman. Smooth bass, sensual groove, modern R&B with trap hi-hats, confident romantic vibe. 30 seconds."),

    ("11_perverts_daily_life", "Perverts Daily Life",
     "Compose a funky comedy anime opening with playful male vocals singing in Brazilian Portuguese about a perverted daily life. Funky bass, comedic timing, cheeky lyrics vibe, upbeat and humorous, slice-of-life comedy style. 30 seconds."),

    ("12_using_eroge_abilities", "Using Eroge Abilities",
     "Compose a video-game inspired anime opening with energetic vocals singing in Brazilian Portuguese about using game abilities in real life. 8-bit chiptune elements mixed with modern EDM, level-up sound effects, gaming power-up feel. 30 seconds."),

    ("13_the_man_who_devours", "The Man Who Devours",
     "Compose a brutal death metal anime opening with guttural male vocals in Brazilian Portuguese about a man who devours everything in his path. Blast beats, crushing guitars, relentless aggression, dark and predatory atmosphere, no mercy. 30 seconds."),

    ("14_warrior_disappointed", "The Warrior Disappointed",
     "Compose a melancholic rock ballad anime opening with emotional male vocals singing in Brazilian Portuguese about a disappointed warrior who lost everything. Start with sad piano, build into powerful rock chorus, bittersweet and epic, redemption arc feel. 30 seconds."),

    ("15_isekai_convenience_store", "Isekai Convenience Store",
     "Compose a quirky J-pop style anime opening with cheerful female vocals singing in Brazilian Portuguese about running a convenience store in another world. Bubbly synths, cute melody, comedic energy, isekai slice-of-life vibes. 30 seconds."),
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
    log("LYRIA — OPENINGS EM PORTUGUES PRA CADA OBRA")
    log("=" * 60)
    log(f"{len(OBRAS)} obras, cada uma com PRO (longa) + CLIP (curta)")
    log("")

    ok_count = 0
    total = len(OBRAS) * 2

    for nome, titulo, prompt in OBRAS:
        log(f"  === {titulo} ===")

        # PRO (longa ~30s)
        out_pro = OUT_DIR / f"{nome}_pro.mp3"
        if out_pro.exists() and out_pro.stat().st_size > 1000:
            log(f"    [PRO] ja existe, pulando")
            ok_count += 1
        else:
            log(f"    [PRO] gerando...")
            ok = call_omniroute(prompt, "openrouter/google/lyria-3-pro-preview", out_pro)
            if ok:
                kb = out_pro.stat().st_size // 1024
                log(f"    [PRO] OK ({kb} KB)")
                ok_count += 1
            else:
                log(f"    [PRO] FALHOU")
            time.sleep(3)

        # CLIP (curta ~15s)
        prompt_clip = prompt.replace("30 seconds", "15 seconds")
        out_clip = OUT_DIR / f"{nome}_clip.mp3"
        if out_clip.exists() and out_clip.stat().st_size > 1000:
            log(f"    [CLIP] ja existe, pulando")
            ok_count += 1
        else:
            log(f"    [CLIP] gerando...")
            ok = call_omniroute(prompt_clip, "openrouter/google/lyria-3-clip-preview", out_clip)
            if ok:
                kb = out_clip.stat().st_size // 1024
                log(f"    [CLIP] OK ({kb} KB)")
                ok_count += 1
            else:
                log(f"    [CLIP] FALHOU")
            time.sleep(3)

        log("")

    log("=" * 60)
    log(f"=== {ok_count}/{total} geradas ===")
    log(f"Pasta: {OUT_DIR}")
    log("")
    log("Estilos por obra:")
    for nome, titulo, _ in OBRAS:
        log(f"  {nome}: {titulo}")


if __name__ == "__main__":
    main()
