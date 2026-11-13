#!/usr/bin/env python3
"""queue-runner.py — Fila serial de capítulos (NUNCA 2 simultâneos).

Protege as chaves Gemini: só começa o próximo capítulo quando o atual
terminar a fase de LLM+TTS (ou seja, quando entrar na fase de código puro: clips, concat, etc).

O ponto de handoff é: quando o narration_cache E os áudios TTS estão prontos.
A partir daí, a montagem é puro FFmpeg (sem API).

Uso:
    python bin/queue-runner.py --caps 2 3 4 5 6 7 8 9
    python bin/queue-runner.py --caps 3-9
    python bin/queue-runner.py --caps 2 --dual   # 4 vídeos (Normal + HyperFrames)

Fluxo por capítulo:
    1. Scrape (tia-fetcher.py)
    2. Split (panel-splitter.py)
    3. LLM + TTS (hiper-pipeline.py — fase que usa chaves)
    4. Montagem de clips (FFmpeg puro — pode rodar em paralelo com scrape do próximo)
    5. Legendas, trilha, censura (FFmpeg puro)
"""
import argparse
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
PYTHON = Path(sys.executable)  # cross-platform: usa o interpretador atual (venv Scripts/python.exe no Windows, venv/bin/python no *nix)
VIDEOS_DIR = PROJECT_DIR / "workspace" / "videos"
LOCK_FILE = PROJECT_DIR / "workspace" / ".queue_lock"


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr)


def is_locked():
    """Verifica se outra instância está rodando."""
    if LOCK_FILE.exists():
        # Checar se o PID dentro do lock ainda está vivo
        try:
            pid = int(LOCK_FILE.read_text().strip())
            os.kill(pid, 0)  # Não mata, só checa se existe
            return True
        except (ValueError, ProcessLookupError, PermissionError):
            # PID morto ou inválido — limpar lock
            LOCK_FILE.unlink(missing_ok=True)
    return False


def acquire_lock():
    if is_locked():
        log("[!] Outra instância do queue-runner está ativa. Saindo.")
        sys.exit(1)
    LOCK_FILE.write_text(str(os.getpid()))


def release_lock():
    LOCK_FILE.unlink(missing_ok=True)


def run_chapter(cap_num, dual=False, obra="the-meek-cat",
                base_url="https://tiamanhwa.com/manhwa/the-meek-cat/capitulo-{n}/"):
    """Executa um capítulo completo: scrape -> split -> pipeline."""
    slug = f"{obra}-cap{cap_num:02d}"
    url = base_url.format(n=cap_num)
    titulo = f"The Meek Cat — Capítulo {cap_num}"
    panels_dir = PROJECT_DIR / "workspace" / "panels" / slug
    cache_dir = PROJECT_DIR / "workspace" / "cache" / slug

    log(f"╔══════════════════════════════════════════╗")
    log(f"║  CAPÍTULO {cap_num}: {titulo}")
    log(f"╚══════════════════════════════════════════╝")

    # Passo 1: Scrape (se não tiver no cache)
    if not cache_dir.exists() or len(list(cache_dir.glob("*.jpg"))) < 5:
        log(f"  ▶ Scrape: {url}")
        r = subprocess.run(
            [str(PYTHON), "bin/tia-fetcher.py", "--url", url, "--slug", slug, "--max-panels", "50"],
            capture_output=True, text=True, timeout=120, cwd=str(PROJECT_DIR)
        )
        if r.returncode != 0:
            log(f"  [X] Scrape falhou: {r.stderr[-200:]}")
            return False
        log(f"  [OK] Scrape OK")
    else:
        log(f"  [OK] Scrape [CACHE]")

    # Passo 2: Split (se não tiver painéis cortados)
    if not panels_dir.exists() or len(list(panels_dir.glob("*.jpg"))) < 10:
        log(f"  ▶ Split")
        r = subprocess.run(
            [str(PYTHON), "bin/panel-splitter.py", "--split",
             "--input", str(cache_dir), "--out", str(panels_dir), "--no-open"],
            capture_output=True, text=True, timeout=120, cwd=str(PROJECT_DIR)
        )
        if r.returncode != 0:
            log(f"  [X] Split falhou: {r.stderr[-200:]}")
            return False
        log(f"  [OK] Split OK")
    else:
        log(f"  [OK] Split [CACHE]")

    # Passo 3: Pipeline
    if dual:
        log(f"  ▶ Dual Pipeline (4 vídeos)")
        cmd = [str(PYTHON), "bin/dual-pipeline.py",
               "--panels-dir", str(panels_dir),
               "--titulo", titulo,
               "--max-panels", "120"]
    else:
        log(f"  ▶ Pipeline Normal (2 vídeos)")
        cmd = [str(PYTHON), "bin/hiper-pipeline.py",
               "--panels-dir", str(panels_dir),
               "--titulo", titulo,
               "--max-panels", "120",
               "--subtitles", "--karaoke", "--censura",
               "--skip-notify"]

    r = subprocess.run(cmd, capture_output=False,
                       timeout=int(os.environ.get("BRANCH_TIMEOUT_S", "21600")), cwd=str(PROJECT_DIR))  # default 6h (era 2h)
    if r.returncode != 0:
        log(f"  [X] Pipeline falhou (exit {r.returncode})")
        return False

    log(f"  [OK] Capítulo {cap_num} — CONCLUÍDO")
    return True


def parse_caps(caps_arg):
    """Parse '3-9' ou '2 3 4 5' para lista de inteiros."""
    result = []
    for item in caps_arg:
        if '-' in item:
            start, end = item.split('-', 1)
            result.extend(range(int(start), int(end) + 1))
        else:
            result.append(int(item))
    return result


def main():
    parser = argparse.ArgumentParser(description="Fila serial de capítulos")
    parser.add_argument("--caps", nargs="+", required=True,
                        help="Números dos capítulos (ex: 3 4 5 ou 3-9)")
    parser.add_argument("--dual", action="store_true",
                        help="Gera 4 vídeos por capítulo (Normal + HyperFrames)")
    parser.add_argument("--obra", default="the-meek-cat")
    args = parser.parse_args()

    caps = parse_caps(args.caps)
    log(f"Fila: {len(caps)} capítulos -> {caps}")
    log(f"Modo: {'Dual (4 vídeos)' if args.dual else 'Normal (2 vídeos)'}")
    log(f"SERIAL: nunca 2 simultâneos (protege chaves Gemini)")

    acquire_lock()
    try:
        done, failed = 0, 0
        for cap in caps:
            ok = run_chapter(cap, dual=args.dual, obra=args.obra)
            if ok:
                done += 1
            else:
                failed += 1
            # Pausa entre capítulos (resfriamento de chaves)
            if cap != caps[-1]:
                log(f"  ⏳ Pausa de 30s entre capítulos (resfriamento de chaves)...")
                time.sleep(30)

        log(f"\n═══ FILA CONCLUÍDA: {done} ok, {failed} falhas ═══")
    finally:
        release_lock()


if __name__ == "__main__":
    main()
