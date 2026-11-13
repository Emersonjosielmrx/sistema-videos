# -*- coding: utf-8 -*-
"""batch_image_gen.py — Teste de carga + geração em massa de imagens via OmniRoute.

Gera ~70 imagens úteis pro pipeline (thumbs, transições, fillers, channel art)
e mede performance/capacidade do gateway.

Uso:
  PYTHONUTF8=1 "D:/recapd-ambientes/producao/venv/Scripts/python.exe" bin/batch_image_gen.py
"""
import json
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import omniroute_image

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT_DIR / "workspace" / "assets" / "generated_batch"

OBRAS = [
    ("Wonderful New World", "wonderful-new-world"),
    ("Perverts Daily Life", "perverts-daily-life"),
    ("What Happens Inside the Dungeon", "what-happens-inside-the-dungeon"),
    ("The Cheat Hitter", "the-cheat-hitter"),
    ("Regressed Warriors", "regressed-warriors"),
    ("Absolute Hypnosis Another World", "absolute-hypnosis-another-world"),
    ("Using Eroge Abilities", "using-eroge-abilities"),
    ("The Man Who Devours", "the-man-who-devours"),
    ("The Inheritor", "the-inheritor"),
    ("The Warrior Disappointed", "the-warrior-disappointed"),
    ("Tremors", "tremors"),
    ("Hero Manager", "hero-manager"),
    ("Isekai Convenience Store", "isekai-convenience-store"),
    ("Taming Noona", "taming-noona"),
    ("The Meek Cat", "the-meek-cat"),
]

MOODS = [
    "tense_dramatic", "sad_emotional", "romantic_sexy",
    "funny_lighthearted", "calm_chill", "neutral_chill",
]

FILLERS = [
    "epic battle scene with energy explosions, manga style, vertical",
    "dark city at night with neon lights, cyberpunk anime style, vertical",
    "peaceful japanese school rooftop at sunset, anime style, vertical",
    "romantic cherry blossom scene, two silhouettes, anime style, vertical",
    "dark dungeon entrance with glowing runes, fantasy anime style, vertical",
    "dramatic ocean storm with lightning, anime style, vertical",
    "cozy bedroom at night with moonlight, slice of life anime, vertical",
    "intense sword clash with sparks flying, action manhwa style, vertical",
    "mysterious forest with glowing mushrooms, fantasy anime, vertical",
    "futuristic mecha hangar, sci-fi anime style, vertical",
    "ancient temple ruins overgrown with vines, adventure anime, vertical",
    "snowy mountain peak at dawn, epic landscape, anime style, vertical",
    "underground fighting arena with crowd, manhwa style, vertical",
    "magical girl transformation sequence background, sparkles and light, vertical",
    "post-apocalyptic wasteland, dramatic sky, dark anime style, vertical",
    "luxury penthouse with city skyline view at night, manhwa style, vertical",
    "volcanic eruption with hero silhouette, epic anime style, vertical",
    "underwater palace with bioluminescent fish, fantasy anime, vertical",
    "haunted mansion hallway with floating candles, horror anime, vertical",
    "racing through a neon tunnel at high speed, anime style, vertical",
]

CHANNEL_ART = [
    "Anime/manhwa channel banner 1280x720, dramatic collage style, dark theme with glowing accents, no text",
    "YouTube channel avatar, anime eye close-up with reflection, circular composition, vibrant colors",
    "Shorts thumbnail template, vertical split with action on left calm on right, anime style, bold contrast",
    "Manhwa recap channel art, stack of manga panels fading into light, cinematic, no text",
    "Subscribe button area background, explosion of color and manga speed lines, anime style",
]


def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


DELAY_BETWEEN_S = 8  # respeitar rate limit do gateway
RETRY_BACKOFF = [15, 30, 60]  # segundos entre retries em caso de 429

def gen_image(prompt, out_path, img_type="filler"):
    """Wrapper que chama omniroute_image._generate com retry em 429."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists() and out_path.stat().st_size > 1000:
        return "cached"

    for attempt, wait in enumerate([0] + RETRY_BACKOFF):
        if wait > 0:
            log(f"    retry #{attempt} em {wait}s...")
            time.sleep(wait)
        omniroute_image._exhausted = False
        ok = omniroute_image._generate(prompt, out_path)
        if ok:
            time.sleep(DELAY_BETWEEN_S)
            return "ok"
    return "fail"


def run():
    results = []
    consecutive_fails = 0
    total_start = time.time()

    # --- THUMBNAILS ---
    log("=== THUMBNAILS (15 obras) ===")
    thumbs_dir = OUT_DIR / "thumbs"
    thumbs_dir.mkdir(parents=True, exist_ok=True)
    for titulo, slug in OBRAS:
        out = thumbs_dir / f"{slug}.png"
        prompt = (
            f"Create a dramatic YouTube thumbnail for a manhwa/anime recap video, "
            f"1280x720 pixels, vibrant colors, dramatic lighting. "
            f"Title: '{titulo}'. Style: anime art with cinematic composition. "
            f"No text overlay, just the visual scene."
        )
        t0 = time.time()
        status = gen_image(prompt, out)
        elapsed = time.time() - t0
        results.append({"type": "thumb", "name": slug, "status": status, "time_s": round(elapsed, 1)})
        log(f"  [{status}] {slug} ({elapsed:.1f}s)")

        if status == "fail":
            consecutive_fails += 1
            if consecutive_fails >= 3:
                log("  ⚠ 3 falhas seguidas — pausa 60s")
                time.sleep(60)
                consecutive_fails = 0
        else:
            consecutive_fails = 0

    # --- TRANSITIONS ---
    log("=== TRANSITIONS (30 pares de mood) ===")
    trans_dir = OUT_DIR / "transitions"
    trans_dir.mkdir(parents=True, exist_ok=True)
    for mood_from in MOODS:
        for mood_to in MOODS:
            if mood_from == mood_to:
                continue
            name = f"{mood_from}__{mood_to}"
            out = trans_dir / f"{name}.png"
            mood_desc = {
                "tense_dramatic": "tense dramatic battlefield",
                "sad_emotional": "melancholic rainy scene",
                "romantic_sexy": "warm romantic sunset",
                "funny_lighthearted": "bright comedic scene",
                "calm_chill": "peaceful serene landscape",
                "neutral_chill": "neutral atmospheric scene",
            }
            desc_from = mood_desc.get(mood_from, mood_from)
            desc_to = mood_desc.get(mood_to, mood_to)
            prompt = (
                f"Create an atmospheric transition illustration, anime/manhwa style, "
                f"1080x1920 vertical, blending from {desc_from} to {desc_to}. "
                f"Abstract, cinematic, suitable as a brief scene separator. "
                f"No text, no characters, just mood and atmosphere."
            )
            t0 = time.time()
            status = gen_image(prompt, out)
            elapsed = time.time() - t0
            results.append({"type": "transition", "name": name, "status": status, "time_s": round(elapsed, 1)})
            log(f"  [{status}] {name} ({elapsed:.1f}s)")

            if status == "fail":
                consecutive_fails += 1
                if consecutive_fails >= 3:
                    log("  ⚠ 3 falhas seguidas — pausa 60s")
                    time.sleep(60)
                    consecutive_fails = 0
            else:
                consecutive_fails = 0

    # --- FILLERS ---
    log("=== FILLERS (20 cenas atmosféricas) ===")
    fillers_dir = OUT_DIR / "fillers"
    fillers_dir.mkdir(parents=True, exist_ok=True)
    for i, desc in enumerate(FILLERS):
        slug = desc[:40].replace(" ", "_").replace(",", "").replace("/", "_")
        out = fillers_dir / f"filler_{i:02d}_{slug}.png"
        prompt = (
            f"Create a manhwa/anime style illustration, 1080x1920 vertical, "
            f"dramatic and atmospheric, high quality. Scene: {desc}"
        )
        t0 = time.time()
        status = gen_image(prompt, out)
        elapsed = time.time() - t0
        results.append({"type": "filler", "name": f"filler_{i:02d}", "status": status, "time_s": round(elapsed, 1)})
        log(f"  [{status}] filler_{i:02d} ({elapsed:.1f}s)")

        if status == "fail":
            consecutive_fails += 1
            if consecutive_fails >= 3:
                log("  ⚠ 3 falhas seguidas — pausa 60s")
                time.sleep(60)
                consecutive_fails = 0
        else:
            consecutive_fails = 0

    # --- CHANNEL ART ---
    log("=== CHANNEL ART (5 peças) ===")
    channel_dir = OUT_DIR / "channel_art"
    channel_dir.mkdir(parents=True, exist_ok=True)
    for i, desc in enumerate(CHANNEL_ART):
        out = channel_dir / f"channel_{i:02d}.png"
        t0 = time.time()
        status = gen_image(desc, out)
        elapsed = time.time() - t0
        results.append({"type": "channel_art", "name": f"channel_{i:02d}", "status": status, "time_s": round(elapsed, 1)})
        log(f"  [{status}] channel_{i:02d} ({elapsed:.1f}s)")

    # --- RELATÓRIO ---
    total_elapsed = time.time() - total_start
    ok_count = sum(1 for r in results if r["status"] == "ok")
    cached_count = sum(1 for r in results if r["status"] == "cached")
    fail_count = sum(1 for r in results if r["status"] == "fail")
    times = [r["time_s"] for r in results if r["status"] == "ok"]
    avg_time = sum(times) / len(times) if times else 0

    report = {
        "total_requested": len(results),
        "generated_ok": ok_count,
        "cached": cached_count,
        "failed": fail_count,
        "total_time_s": round(total_elapsed, 1),
        "avg_time_per_image_s": round(avg_time, 1),
        "success_rate_pct": round((ok_count + cached_count) / max(len(results), 1) * 100, 1),
        "details": results,
    }

    report_path = OUT_DIR / "_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    log(f"\n{'='*50}")
    log(f"RELATÓRIO FINAL")
    log(f"  Total solicitadas: {len(results)}")
    log(f"  Geradas com sucesso: {ok_count}")
    log(f"  Cache hit: {cached_count}")
    log(f"  Falhas: {fail_count}")
    log(f"  Tempo total: {total_elapsed:.0f}s ({total_elapsed/60:.1f} min)")
    log(f"  Tempo médio/imagem: {avg_time:.1f}s")
    log(f"  Taxa de sucesso: {report['success_rate_pct']}%")
    log(f"  Relatório salvo: {report_path}")
    log(f"{'='*50}")


if __name__ == "__main__":
    run()
