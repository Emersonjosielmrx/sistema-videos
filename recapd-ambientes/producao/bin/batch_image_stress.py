# -*- coding: utf-8 -*-
"""batch_image_stress.py — Teste de carga MÁXIMO de imagens via OmniRoute.

Estratégia:
- Lê textos reais dos capítulos (narration_cache) pra gerar prompts contextuais
- Opera em LOTES DE 10 com pausa entre lotes (evita burst 429)
- Continua até falhar em um lote inteiro (= quota real esgotada)
- Registra throughput real: imagens/min, total antes de esgotar

Uso:
  PYTHONUTF8=1 "D:/recapd-ambientes/producao/venv/Scripts/python.exe" bin/batch_image_stress.py
"""
import json
import time
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import omniroute_image

PROJECT_DIR = Path(__file__).resolve().parent.parent
NARRATION_DIR = PROJECT_DIR / "workspace" / "narration_cache"
OUT_DIR = PROJECT_DIR / "workspace" / "assets" / "stress_test_images"

BATCH_SIZE = 10
PAUSE_BETWEEN_BATCHES_S = 45
DELAY_WITHIN_BATCH_S = 5
MAX_CONSECUTIVE_BATCH_FAILS = 2


def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def extract_context_from_cap(json_path):
    """Extrai resumo do capítulo a partir das locucoes."""
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception:
        try:
            data = json.loads(json_path.read_text(encoding="latin-1"))
        except Exception:
            return None

    titulo = data.get("titulo_video", "")
    locs = data.get("locucoes", [])
    if not locs:
        return None

    texts = [loc.get("text", "") for loc in locs[:10]]
    combined = " ".join(texts)[:600]

    personas = set(loc.get("persona", "") for loc in locs if loc.get("persona"))
    personas.discard("Narrador")
    personas.discard("Narradora")

    return {
        "titulo": titulo,
        "resumo": combined,
        "personagens": list(personas)[:5],
        "n_panels": len(locs),
    }


def build_prompt_from_context(ctx, img_type="thumb"):
    """Gera prompt de imagem baseado no contexto real do capítulo."""
    titulo = ctx["titulo"]
    resumo = ctx["resumo"][:200]
    chars = ", ".join(ctx["personagens"][:3]) if ctx["personagens"] else "protagonista misterioso"

    if img_type == "thumb":
        return (
            f"Create a dramatic YouTube thumbnail 1280x720 for an anime/manhwa recap video. "
            f"Scene context: {resumo} "
            f"Characters: {chars}. "
            f"Style: cinematic anime art, vibrant colors, dramatic lighting, no text overlay."
        )
    elif img_type == "scene":
        return (
            f"Create a vertical 1080x1920 anime/manhwa illustration. "
            f"Scene: {resumo} "
            f"Characters involved: {chars}. "
            f"Style: detailed manga panel art, atmospheric, dramatic composition."
        )
    elif img_type == "mood":
        return (
            f"Create an abstract atmospheric vertical illustration 1080x1920. "
            f"Mood inspired by: {resumo[:100]} "
            f"Style: anime background art, no characters, cinematic lighting, emotional."
        )
    return f"Anime illustration: {resumo[:150]}"


def collect_jobs():
    """Coleta todos os jobs possíveis a partir dos narration_cache."""
    jobs = []
    cache_files = sorted(NARRATION_DIR.glob("*.json"))

    for f in cache_files:
        name = f.stem
        if "_sk1_" in name or "_sk2_" in name:
            continue

        ctx = extract_context_from_cap(f)
        if not ctx:
            continue

        slug = re.sub(r"_\d+panels$", "", name)

        jobs.append({
            "name": f"{slug}_thumb",
            "prompt": build_prompt_from_context(ctx, "thumb"),
            "out": OUT_DIR / "thumbs" / f"{slug}.png",
        })
        jobs.append({
            "name": f"{slug}_scene",
            "prompt": build_prompt_from_context(ctx, "scene"),
            "out": OUT_DIR / "scenes" / f"{slug}.png",
        })
        jobs.append({
            "name": f"{slug}_mood",
            "prompt": build_prompt_from_context(ctx, "mood"),
            "out": OUT_DIR / "moods" / f"{slug}.png",
        })

    return jobs


def gen_one(prompt, out_path):
    """Gera uma imagem. Retorna 'ok', 'cached', ou 'fail'."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists() and out_path.stat().st_size > 1000:
        return "cached"
    omniroute_image._exhausted = False
    ok = omniroute_image._generate(prompt, out_path)
    return "ok" if ok else "fail"


def run():
    jobs = collect_jobs()
    log(f"Total de jobs coletados: {len(jobs)} (de {len(list(NARRATION_DIR.glob('*.json')))} narration files)")
    log(f"Lotes de {BATCH_SIZE}, pausa {PAUSE_BETWEEN_BATCHES_S}s entre lotes")
    log(f"Pasta de saída: {OUT_DIR}")
    log("=" * 60)

    results = []
    batch_num = 0
    consecutive_batch_fails = 0
    total_start = time.time()

    for i in range(0, len(jobs), BATCH_SIZE):
        batch = jobs[i:i + BATCH_SIZE]
        batch_num += 1
        batch_ok = 0
        batch_fail = 0
        batch_cached = 0

        log(f"\n--- LOTE {batch_num} ({i+1}-{i+len(batch)}/{len(jobs)}) ---")

        for j, job in enumerate(batch):
            t0 = time.time()
            status = gen_one(job["prompt"], job["out"])
            elapsed = time.time() - t0

            results.append({
                "name": job["name"],
                "status": status,
                "time_s": round(elapsed, 1),
                "batch": batch_num,
            })

            if status == "ok":
                batch_ok += 1
                log(f"  [{status}] {job['name']} ({elapsed:.1f}s)")
                if j < len(batch) - 1:
                    time.sleep(DELAY_WITHIN_BATCH_S)
            elif status == "cached":
                batch_cached += 1
            else:
                batch_fail += 1
                log(f"  [{status}] {job['name']} ({elapsed:.1f}s)")

        log(f"  Lote {batch_num}: {batch_ok} ok, {batch_cached} cached, {batch_fail} fail")

        if batch_fail == len(batch) - batch_cached:
            consecutive_batch_fails += 1
            log(f"  ⚠ Lote inteiro falhou ({consecutive_batch_fails}/{MAX_CONSECUTIVE_BATCH_FAILS})")
            if consecutive_batch_fails >= MAX_CONSECUTIVE_BATCH_FAILS:
                log("  ✗ QUOTA ESGOTADA — parando teste de carga")
                break
        else:
            consecutive_batch_fails = 0

        if i + BATCH_SIZE < len(jobs) and batch_ok > 0:
            log(f"  Pausa {PAUSE_BETWEEN_BATCHES_S}s antes do próximo lote...")
            time.sleep(PAUSE_BETWEEN_BATCHES_S)

    # --- RELATÓRIO ---
    total_elapsed = time.time() - total_start
    ok_count = sum(1 for r in results if r["status"] == "ok")
    cached_count = sum(1 for r in results if r["status"] == "cached")
    fail_count = sum(1 for r in results if r["status"] == "fail")
    times = [r["time_s"] for r in results if r["status"] == "ok"]
    avg_time = sum(times) / len(times) if times else 0
    imgs_per_min = ok_count / (total_elapsed / 60) if total_elapsed > 0 else 0

    report = {
        "test_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "config": {
            "batch_size": BATCH_SIZE,
            "pause_between_batches_s": PAUSE_BETWEEN_BATCHES_S,
            "delay_within_batch_s": DELAY_WITHIN_BATCH_S,
        },
        "total_jobs": len(jobs),
        "attempted": len(results),
        "generated_ok": ok_count,
        "cached": cached_count,
        "failed": fail_count,
        "batches_completed": batch_num,
        "total_time_s": round(total_elapsed, 1),
        "total_time_min": round(total_elapsed / 60, 1),
        "avg_time_per_image_s": round(avg_time, 1),
        "images_per_minute": round(imgs_per_min, 2),
        "success_rate_pct": round((ok_count + cached_count) / max(len(results), 1) * 100, 1),
        "models_used": omniroute_image.MODELS,
        "details": results,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = OUT_DIR / "_stress_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    log(f"\n{'=' * 60}")
    log(f"RELATÓRIO — TESTE DE CARGA")
    log(f"  Jobs totais disponíveis: {len(jobs)}")
    log(f"  Tentados: {len(results)}")
    log(f"  Geradas com sucesso: {ok_count}")
    log(f"  Cache hit: {cached_count}")
    log(f"  Falhas: {fail_count}")
    log(f"  Lotes completados: {batch_num}")
    log(f"  Tempo total: {total_elapsed:.0f}s ({total_elapsed/60:.1f} min)")
    log(f"  Tempo médio/imagem: {avg_time:.1f}s")
    log(f"  Throughput: {imgs_per_min:.2f} imgs/min")
    log(f"  Taxa de sucesso: {report['success_rate_pct']}%")
    log(f"  Relatório: {report_path}")
    log(f"{'=' * 60}")


if __name__ == "__main__":
    run()
