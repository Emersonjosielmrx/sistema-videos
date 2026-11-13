"""
FÁBRICA DE VÍDEO (fase paralela — só ffmpeg, NÃO toca no Gemini).

Consome os marcadores <slug>.audio_ready que a fábrica de áudio deixou e
renderiza o vídeo completo (pipeline normal, SEM --audio-only). Como todo TTS
já está no cache, é ffmpeg puro -> pode rodar VÁRIOS caps em paralelo.

Estados (workspace/factory_state/):
    <slug>.audio_ready    -> áudio pronto, esperando render (produzido pela fábrica de áudio)
    <slug>.video_running  -> render em andamento (evita disparo duplo)
    <slug>.video_done     -> vídeo validado (ffprobe OK)

Regras:
- Nunca renderiza um cap sem .audio_ready (senão gastaria Gemini).
- Limite de renders simultâneos (MAX_PARALLEL) pra não estourar CPU/RAM.
- Valida a saída com ffprobe; se OK grava .video_done, senão remove .video_running
  pra tentar de novo no próximo ciclo.

Rodar a cada ~5 min por cron. Idempotente.
"""
import subprocess
import os
import sys
import datetime
import threading
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROJECT = Path(__file__).resolve().parent.parent
PY = PROJECT / "venv" / "Scripts" / "python.exe"
STATE = PROJECT / "workspace" / "factory_state"
VIDEOS = PROJECT / "workspace" / "videos"
LOGS = PROJECT / "logs"
STATE.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)

TITULO_FMT = "O Guerreiro Regressou — Capitulo {}"
MAX_PARALLEL = 2   # ffmpeg é pesado; 2 renders simultâneos é o teto seguro


def log(msg):
    line = f"[{datetime.datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line)
    with open(LOGS / "factory.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def cap_num(slug: str) -> int:
    return int(slug.rsplit("cap", 1)[-1])


def running_renders() -> int:
    return len(list(STATE.glob("*.video_running")))


def ffprobe_ok(mp4: Path) -> bool:
    """Vídeo válido: tem duração e o áudio não é >5s menor que o vídeo."""
    def dur(stream):
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-select_streams", stream,
             "-show_entries", "stream=duration", "-of", "csv=p=0", str(mp4)],
            capture_output=True, text=True)
        try:
            return float(r.stdout.strip().splitlines()[0])
        except Exception:
            return 0.0
    v, a = dur("v:0"), dur("a:0")
    if v <= 1.0:
        return False
    if a and (v - a) > 5.0:
        log(f"  [!] {mp4.name}: áudio {a:.1f}s vs vídeo {v:.1f}s (>5s de diff) — QUEBRADO")
        return False
    return True


def find_output(slug: str, n: int) -> Path | None:
    """Acha o _CENSURADO_ULTIMO.mp4 mais recente do cap (ou _ULTIMO se sem censura)."""
    pats = [f"hipercool_*capitulo-{n}_*_CAP{n:02d}_CENSURADO_ULTIMO.mp4",
            f"hipercool_*capitulo-{n}_*_CAP{n:02d}_ULTIMO.mp4"]
    for pat in pats:
        hits = sorted(VIDEOS.glob(pat), key=lambda p: p.stat().st_mtime, reverse=True)
        if hits:
            return hits[0]
    return None


def render(slug: str):
    n = cap_num(slug)
    running = STATE / f"{slug}.video_running"
    running.write_text(datetime.datetime.now().isoformat(), encoding="utf-8")
    log(f"▶ Render iniciado: {slug} (cap {n})")

    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["TTS_ENGINE"] = "gemini"
    env["PANEL_FX"] = "1"
    env["GEMINI_TTS_PROXY_ENABLED"] = "1"
    env["CENSURA_BRANCO_VAR"] = "B2"
    # FASE DE VÍDEO = ffmpeg puro. Proíbe chamar o Gemini: fala sem cache vira
    # clip rápido em vez de travar na quota 429. A voz é feita pela fábrica de áudio.
    env["TTS_CACHE_ONLY"] = "1"

    log_path = LOGS / f"video_cap{n:02d}.log"
    args = [
        str(PY), "bin/hiper-pipeline.py",
        "--panels-dir", f"workspace/panels/{slug}",
        "--titulo", TITULO_FMT.format(n),
        "--narrator-gender", "M",
        "--max-panels", "120",
        "--subtitles", "--karaoke", "--censura", "--skip-notify",
        "--output-suffix", f"_CAP{n:02d}",
    ]
    with open(log_path, "w", encoding="utf-8") as lf:
        rc = subprocess.run(args, cwd=str(PROJECT), env=env,
                            stdout=lf, stderr=subprocess.STDOUT).returncode

    out = find_output(slug, n)
    if rc == 0 and out and ffprobe_ok(out):
        (STATE / f"{slug}.video_done").write_text(
            f"{datetime.datetime.now().isoformat()} {out.name}\n", encoding="utf-8")
        running.unlink(missing_ok=True)
        log(f"✅ Render OK e validado: {slug} -> {out.name}")
    else:
        running.unlink(missing_ok=True)  # libera pra retry no próximo ciclo
        log(f"❌ Render falhou/inválido: {slug} (rc={rc}). Vai tentar de novo.")


def main():
    log("── video_factory: ciclo ──")
    slots = MAX_PARALLEL - running_renders()
    if slots <= 0:
        log(f"{running_renders()} render(s) em andamento (teto={MAX_PARALLEL}). Aguardando.")
        return

    pend = []
    for m in sorted(STATE.glob("*.audio_ready")):
        slug = m.stem
        if (STATE / f"{slug}.video_done").exists():
            continue
        if (STATE / f"{slug}.video_running").exists():
            continue
        pend.append(slug)

    if not pend:
        log("Nenhum cap com áudio pronto aguardando render.")
        return

    to_start = pend[:slots]
    log(f"Slots livres: {slots}. Disparando: {', '.join(to_start)}")
    threads = [threading.Thread(target=render, args=(s,), daemon=False) for s in to_start]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


if __name__ == "__main__":
    main()
