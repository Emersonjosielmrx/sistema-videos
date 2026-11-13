"""
FÁBRICA DE ÁUDIO (fase serial — protege a quota do Gemini TTS).

Regra de ouro: NUNCA mais de um --audio-only rodando ao mesmo tempo.
- Checa se já há um hiper-pipeline.py --audio-only vivo → se sim, aborta o ciclo.
- Acha o menor capNN pendente (02..88, pula 01 e 11 que já estão prontos) que:
    tem pasta de painéis E ainda não tem o marcador <slug>.audio_ready.
- Dispara UM hiper-pipeline.py --audio-only em background (env limpo, sem o bug
  do `set X=1&&` — passamos as vars por dict, não por string de shell).
- O próprio pipeline grava workspace/factory_state/<slug>.audio_ready no fim.
- A fábrica de VÍDEO (video_factory.py) consome esses marcadores e renderiza em
  paralelo, reusando o cache de TTS (ffmpeg puro, sem tocar no Gemini).

Rodar a cada ~5-10 min por cron. Idempotente.
"""
import subprocess
import os
import sys
import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROJECT = Path(__file__).resolve().parent.parent
PY = Path("D:/recapd-ambientes/producao/venv/Scripts/python.exe")  # FIX usa o venv do worker
PANELS = PROJECT / "workspace" / "panels"
STATE = PROJECT / "workspace" / "factory_state"
LOGS = PROJECT / "logs"
STATE.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)

SLUG_FMT = "regressed-warriors-cap{:02d}"
TITULO_FMT = "O Guerreiro Regressou — Capitulo {}"
CAP_RANGE = range(2, 89)      # 02..88
SKIP = {1, 11}                # já prontos


def log(msg):
    line = f"[{datetime.datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line)
    with open(LOGS / "factory.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def audio_pipeline_running() -> bool:
    """True se JÁ existe um hiper-pipeline.py --audio-only vivo (serial guard).

    Filtra por name='python.exe' pra o PRÓPRIO wmic (cuja linha de comando
    contém a string procurada) não contar como falso positivo. A checagem dos
    marcadores é feita em Python, sobre a linha de comando de cada python.exe.
    """
    r = subprocess.run(
        ["wmic", "process", "where", "name='python.exe'",
         "get", "commandline"],
        capture_output=True, text=True)
    for ln in r.stdout.splitlines():
        if "hiper-pipeline.py" in ln and "--audio-only" in ln:
            return True
    return False


def next_pending_cap():
    for n in CAP_RANGE:
        if n in SKIP:
            continue
        slug = SLUG_FMT.format(n)
        if not (PANELS / slug).is_dir():
            continue
        if (STATE / f"{slug}.audio_ready").exists():
            continue
        return n
    return None


def main():
    log("── audio_factory: ciclo ──")

    if audio_pipeline_running():
        log("Já há um --audio-only rodando. Serial protegido, abortando ciclo.")
        return

    n = next_pending_cap()
    if n is None:
        log("Nenhum capítulo pendente de áudio. Fábrica de áudio ociosa.")
        return

    slug = SLUG_FMT.format(n)
    log(f"Próximo cap de áudio: {slug} (cap {n})")

    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["TTS_ENGINE"] = "eleven"   # ElevenLabs (6 chaves com crédito) — NÃO gemini (quota estourada)
    env["GEMINI_TTS_PROXY_ENABLED"] = "1"

    log_path = LOGS / f"audio_cap{n:02d}.log"
    args = [
        str(PY), "bin/hiper-pipeline.py",
        "--panels-dir", f"workspace/panels/{slug}",
        "--titulo", TITULO_FMT.format(n),
        "--narrator-gender", "M",
        "--max-panels", "120",
        "--subtitles", "--karaoke", "--censura", "--skip-notify",
        "--audio-only",
        "--output-suffix", f"_CAP{n:02d}",
    ]
    with open(log_path, "w", encoding="utf-8") as lf:
        subprocess.Popen(args, cwd=str(PROJECT), env=env,
                         stdout=lf, stderr=subprocess.STDOUT)
    log(f"Disparado --audio-only p/ {slug} → {log_path.name} (background).")


if __name__ == "__main__":
    main()
