# -*- coding: utf-8 -*-
"""queue_runner.py — Fila serial de vídeos (equivalente ao queue-runner do hipercool).

Executa N vídeos sequencialmente, respeitando COMMAND_STOP/PAUSE/SKIP.
Cada job gera um vídeo completo via story_pipeline.run().
"""
import os
import sys
import json
import time
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hp_common import PROJECT_DIR, log
from story_pipeline import run, _check_command_files, PRESETS

# Proxy bypass — Webshare agotado (402) em 2026-07-13, ativa fallback IP direto pro TTS
os.environ.setdefault("EDGE_TTS_ALLOW_DIRECT", "1")

QUEUE_FILE = PROJECT_DIR / "workspace" / "queue.json"
QUEUE_LOG = PROJECT_DIR / "logs" / "queue_runner.log"
PROGRESS_FILE = PROJECT_DIR / "workspace" / "queue_progress.json"


def _log_to_file(msg):
    QUEUE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(QUEUE_LOG, "a", encoding="utf-8") as f:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{ts}] {msg}\n")


# ── Métricas por vídeo (gravadas em JSONL para análise futura) ───────────────
try:
    import psutil
    _HAS_PSUTIL = True
except Exception:
    _HAS_PSUTIL = False

_METRICS_FILE = PROJECT_DIR / "logs" / "pipeline_metrics.jsonl"


def _parse_api_events():
    """Lê os últimos 16KB do log e extrai eventos de API pra popolar counters."""
    try:
        with open(QUEUE_LOG, "rb") as f:
            f.seek(max(0, f.seek(0, 2) - 16384))
            tail = f.read().decode("utf-8", errors="ignore")
        c = {}
        e = []
        for line in tail.splitlines():
            if "pollinations" in line and "ok" in line:
                c["img_pollinations"] = c.get("img_pollinations", 0) + 1
            if "402" in line:
                c["api_402"] = c.get("api_402", 0) + 1
                e.append({"t": 0, "tipo": "api_402", "d": line.strip()[:120]})
            if "429" in line:
                c["api_429"] = c.get("api_429", 0) + 1
                e.append({"t": 0, "tipo": "api_429", "d": line.strip()[:120]})
            if "proxy" in line and ("402" in line or "failed" in line.lower()):
                c["proxy_fail"] = c.get("proxy_fail", 0) + 1
            if "edge-tts direct" in line and "[OK]" in line:
                c["tts_direct_ok"] = c.get("tts_direct_ok", 0) + 1
            if "quarantine" in line.lower() or "QUARENTENA" in line:
                c["quarantine"] = c.get("quarantine", 0) + 1
                e.append({"t": 0, "tipo": "quarantine", "d": line.strip()[:120]})
        return c, e
    except Exception:
        return {}, []


def _new_metrics(genero):
    """Abre um tracker de métricas para o próximo vídeo."""
    return {
        "genero": genero,
        "t_start": time.time(),
        "ram_before_gb": psutil.virtual_memory().used / (1024**3) if _HAS_PSUTIL else 0.0,
    }


def _finalize_metrics(mt, status, result, disk_free_gb, error=None):
    """Fecha o tracker e grava 1 linha JSONL em pipeline_metrics.jsonl."""
    import json as _json
    elapsed = round(time.time() - mt["t_start"], 2)
    api_counters, api_events = _parse_api_events()

    record = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "genero": mt["genero"],
        "status": status,
        "elapsed_s": elapsed,
        "counters": api_counters,
        "events": api_events,
        "hw": {},
        "error": str(error) if error else None,
    }

    if _HAS_PSUTIL:
        vm = psutil.virtual_memory()
        record["hw"] = {
            "ram_used_gb": round(psutil.Process().memory_info().rss / (1024**3), 2),
            "ram_total_gb": round(vm.total / (1024**3), 1),
            "ram_pct": vm.percent,
            "cpu_pct": psutil.cpu_percent(interval=None),
            "disk_free_gb": round(disk_free_gb, 1) if disk_free_gb else None,
            "ram_before_gb": round(mt.get("ram_before_gb", 0), 2),
        }

    if result:
        record.update({
            "video_path": result.get("video"),
            "story_id": result.get("story_id"),
            "video_duration_s": result.get("duracao_s", 0),
            "tempo_geracao_s": result.get("tempo_geracao_s", 0),
            "n_cenas": result.get("n_cenas", 0),
            "warnings": result.get("warnings", []),
        })

    try:
        _METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_METRICS_FILE, "a", encoding="utf-8") as f:
            f.write(_json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        _log_to_file(f"[metrics] falha ao gravar: {e}")


def _save_progress(progress):
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_FILE.write_text(json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_progress():
    if PROGRESS_FILE.exists():
        try:
            return json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"completed": [], "last_index": -1}


def load_queue(queue_file=None):
    """Carrega fila de um JSON. Formato: lista de dicts com genero/tema/cenas/preset."""
    qf = Path(queue_file) if queue_file else QUEUE_FILE
    if not qf.exists():
        return []
    return json.loads(qf.read_text(encoding="utf-8"))


def generate_queue(generos=None, n_per_genero=3, preset="final"):
    """Gera fila automática variando gêneros."""
    generos = generos or ["superacao", "romance", "terror", "comedia", "drama", "fantasia"]
    queue = []
    for g in generos:
        for i in range(n_per_genero):
            queue.append({
                "genero": g,
                "tema": None,
                "preset": preset,
                "suffix": f"_{g}_{i+1}",
            })
    return queue


def run_queue(queue, skip_notify=True, stop_on_fail=False, resume=True):
    """Executa a fila sequencialmente com suporte a resume."""
    total = len(queue)
    results = []

    # Resume: pula jobs já completados
    progress = _load_progress() if resume else {"completed": [], "last_index": -1}
    start_idx = progress["last_index"] + 1 if resume else 0

    if start_idx > 0:
        log(f"QUEUE RUNNER: retomando do job {start_idx + 1}/{total}")
        _log_to_file(f"Retomando fila do job {start_idx + 1}")

    log(f"QUEUE RUNNER: {total} videos na fila (iniciando em {start_idx + 1})")
    _log_to_file(f"Iniciando fila com {total} jobs (start={start_idx + 1})")

    for i in range(start_idx, total):
        job = queue[i]
        if _check_command_files():
            log(f"SKIP detectado no job {i+1}")
            results.append({"job": i+1, "status": "skipped"})
            continue

        log(f"\n{'='*50}")
        log(f"QUEUE [{i+1}/{total}]: {job.get('genero', '?')} — {job.get('tema', 'aleatorio')}")
        log(f"{'='*50}")

        t0 = time.time()
        _mt = _new_metrics(job.get("genero", "superacao"))
        try:
            result = run(
                genero=job.get("genero", "superacao"),
                tema=job.get("tema"),
                n_cenas=job.get("cenas"),
                preset=job.get("preset", "final"),
                quality=job.get("quality", "med"),
                output_suffix=job.get("suffix", f"_q{i+1}"),
                skip_notify=skip_notify,
                censura=job.get("censura", False),
            )
            elapsed = time.time() - t0
            status = "ok" if result else "failed"
            results.append({"job": i+1, "status": status, "time": round(elapsed),
                           "video": result.get("video") if result else None})
            _log_to_file(f"Job {i+1}/{total}: {status} ({elapsed:.0f}s)")
            _finalize_metrics(_mt, status, result, None)

            # Salvar progresso após cada job
            progress["last_index"] = i
            if status == "ok":
                progress["completed"].append(i)
            _save_progress(progress)

            if not result and stop_on_fail:
                log("STOP_ON_FAIL: abortando fila")
                break

        except Exception as e:
            elapsed = time.time() - t0
            results.append({"job": i+1, "status": "error", "error": str(e), "time": round(elapsed)})
            _log_to_file(f"Job {i+1}/{total}: ERROR — {e}")
            _finalize_metrics(_mt, "error", None, None, error=str(e))
            progress["last_index"] = i
            _save_progress(progress)
            if stop_on_fail:
                break

        time.sleep(2)

    ok = sum(1 for r in results if r.get("status") == "ok")
    total_done = start_idx + len(results)
    log(f"\nQUEUE COMPLETA: {ok}/{len(results)} videos gerados (total processados: {total_done}/{total})")
    _log_to_file(f"Fila completa: {ok}/{len(results)}")

    # Limpa progresso se terminou tudo
    if total_done >= total and PROGRESS_FILE.exists():
        PROGRESS_FILE.unlink()

    try:
        from _tg_safe import send_telegram
        send_telegram(f"Fila completa: {ok}/{len(results)} videos gerados")
    except Exception:
        pass

    return results


def run_continuous(preset="night", generos=None, max_videos=50, sleep_between=120):
    """Modo producao continua: gera videos infinitamente ate COMMAND_STOP ou disco cheio.

    Varia genero ciclicamente, valida cada video, dorme entre geracoes.
    Para automaticamente se disco <10GB livre.
    """
    import shutil
    generos = generos or ["superacao", "romance", "terror", "comedia", "drama", "fantasia",
                          "misterio", "motivacional", "curiosidades", "religioso"]
    results = []
    genre_idx = 0

    log(f"CONTINUOUS MODE: max {max_videos} videos, preset={preset}, sleep={sleep_between}s")
    _log_to_file(f"Continuous mode iniciado: max={max_videos}, preset={preset}")

    for video_num in range(1, max_videos + 1):
        if _check_command_files():
            log("CONTINUOUS: COMMAND_STOP detectado — parando")
            break

        free_gb = shutil.disk_usage(str(PROJECT_DIR)).free / (1024**3)
        if free_gb < 10:
            log(f"CONTINUOUS: disco com apenas {free_gb:.1f}GB livre — parando")
            _log_to_file(f"Disco cheio ({free_gb:.1f}GB), parando apos {video_num-1} videos")
            break

        genero = generos[genre_idx % len(generos)]
        genre_idx += 1

        log(f"\n{'='*50}")
        log(f"CONTINUOUS [{video_num}/{max_videos}]: {genero} (disco: {free_gb:.0f}GB livre)")
        log(f"{'='*50}")

        t0 = time.time()
        _mt = _new_metrics(genero)
        try:
            result = run(
                genero=genero,
                tema=None,
                preset=preset,
                output_suffix=f"_auto_{video_num:03d}",
                skip_notify=True,
            )
            elapsed = time.time() - t0
            status = "ok" if result else "failed"
            results.append({"num": video_num, "genero": genero, "status": status,
                           "time": round(elapsed), "video": result.get("video") if result else None})
            _log_to_file(f"Continuous {video_num}: {genero} — {status} ({elapsed:.0f}s)")
            _finalize_metrics(_mt, status, result, free_gb)

        except Exception as e:
            elapsed = time.time() - t0
            results.append({"num": video_num, "genero": genero, "status": "error", "error": str(e)})
            _log_to_file(f"Continuous {video_num}: {genero} — ERROR ({e})")
            _finalize_metrics(_mt, "error", None, free_gb, error=str(e))

        if video_num < max_videos:
            log(f"  Dormindo {sleep_between}s antes do proximo...")
            time.sleep(sleep_between)

    ok = sum(1 for r in results if r.get("status") == "ok")
    log(f"\nCONTINUOUS COMPLETO: {ok}/{len(results)} videos gerados")
    _log_to_file(f"Continuous completo: {ok}/{len(results)}")
    return results


def main():
    parser = argparse.ArgumentParser(description="Queue Runner — fila serial de videos")
    parser.add_argument("--queue-file", default=None, help="JSON com lista de jobs")
    parser.add_argument("--generos", nargs="+", default=None, help="Generos pra gerar")
    parser.add_argument("--n-per-genero", type=int, default=3)
    parser.add_argument("--preset", default="final", choices=list(PRESETS.keys()) + ["continuous"])
    parser.add_argument("--stop-on-fail", action="store_true")
    parser.add_argument("--notify", action="store_true")
    parser.add_argument("--no-resume", action="store_true", help="Ignora progresso anterior")
    parser.add_argument("--continuous", action="store_true", help="Modo producao continua autonoma")
    parser.add_argument("--max-videos", type=int, default=50, help="Max videos no modo continuous")
    parser.add_argument("--sleep", type=int, default=120, help="Segundos entre videos (continuous)")

    args = parser.parse_args()

    if args.continuous:
        preset = args.preset if args.preset != "final" else "night"
        results = run_continuous(preset=preset, generos=args.generos,
                                 max_videos=args.max_videos, sleep_between=args.sleep)
    elif args.queue_file:
        queue = load_queue(args.queue_file)
        if not queue:
            print("Fila vazia — nada a fazer")
            return
        results = run_queue(queue, skip_notify=not args.notify, stop_on_fail=args.stop_on_fail,
                             resume=not args.no_resume)
    else:
        queue = generate_queue(generos=args.generos, n_per_genero=args.n_per_genero,
                               preset=args.preset)
        if not queue:
            print("Fila vazia — nada a fazer")
            return
        results = run_queue(queue, skip_notify=not args.notify, stop_on_fail=args.stop_on_fail,
                             resume=not args.no_resume)

    summary_path = PROJECT_DIR / "logs" / "queue_results.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Resultados em: {summary_path}")


if __name__ == "__main__":
    main()
