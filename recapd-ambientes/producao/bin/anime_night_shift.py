#!/usr/bin/env python3
"""anime_night_shift.py — driver noturno para anime_auto.py.

Executa anime_auto.py em loop infinito, dormindo entre rodadas.
Diferenças do infinite_nightshift.sh (bash):
  - Trata exceções Python que o bash ignora
  - Detecta especificamente "429 quota" e espera 5 min (não 70s)
  - Detecta "Nenhum candidato short" (pool vazio) e espera 3 min
  - Detecta "Nenhum candidato deitado" e espera 3 min
  - Detecta "sem transcrição" (Whisper falhou) e marca o vídeo pra pular
  - Log estruturado em workspace/anime_nightshift.log
  - Persiste estado em workspace/anime_nightshift_state.json
  - Health-check do worker PC2 (se configurado)

Uso:
  PYTHONUTF8=1 venv/Scripts/python.exe bin/anime_night_shift.py --modo short --top 3
  PYTHONUTF8=1 venv/Scripts/python.exe bin/anime_night_shift.py --modo deitado --top 2
"""
import os
import sys
import time
import json
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# ── configuração ──────────────────────────────────────────────
PROJECT_DIR = Path(__file__).resolve().parent.parent
WORKSPACE = PROJECT_DIR / "workspace" / "anime"
LOG_FILE = PROJECT_DIR / "workspace" / "anime_nightshift.log"
STATE_FILE = PROJECT_DIR / "workspace" / "anime_nightshift_state.json"
PIDFILE = PROJECT_DIR / "workspace" / ".anime_nightshift.pid"

# Worker PC2 (opcional — se configurado, despacha para lá)
WORKER_HOST = os.environ.get("ANIME_WORKER_HOST", "")  # ex: "192.168.18.7"
WORKER_PORT = int(os.environ.get("ANIME_WORKER_PORT", "8771"))

AUTO_PY = PROJECT_DIR / "bin" / "anime_auto.py"
PYTHON = Path(sys.executable)

# Cooldown por tipo de erro (segundos)
COOLDOWN = {
    "quota_429": 300,        # 5 min — quota Gemini
    "no_candidates": 180,    # 3 min — pool de candidatos vazio
    "no_transcript": 120,    # 2 min — sem legenda/Whisper
    "pipeline_error": 240,    # 4 min — pipeline explodiu
    "success": 30,           # 30s — sucesso, próximo vídeo
    "unknown": 120,          # 2 min — erro desconhecido
}


def log(msg, level="INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{ts} [{level}] {msg}"
    print(line)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def load_state():
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"runs": 0, "successes": 0, "failures": 0, "last_error": None,
                "last_run": None, "last_mode": None, "consecutive_fails": 0,
                "skipped_videos": []}


def save_state(st):
    try:
        STATE_FILE.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def _pid_alive(pid):
    if pid is None:
        return False
    try:
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                             capture_output=True, text=True, timeout=15).stdout
        return str(pid) in out
    except Exception:
        return False


def _write_pid():
    try:
        PIDFILE.write_text(str(os.getpid()))
    except Exception:
        pass


def _detect_error_type(output):
    """Detecta o tipo de erro no output para ajustar o cooldown."""
    out = output.lower()
    if "429" in out or "quota" in out or "billing" in out:
        return "quota_429"
    if "nenhum candidato" in out or "no candidates" in out or "pool vazio" in out:
        return "no_candidates"
    if "sem transcrição" in out or "sem legenda" in out or "no transcript" in out:
        return "no_transcript"
    if "pipeline falhou" in out or "rc=" in out or "error" in out:
        return "pipeline_error"
    return "unknown"


def run_anime_auto(modo, engine, top, dry_run=False):
    """Executa uma rodada do anime_auto.py e retorna (success, cooldown_type, output)."""
    cmd = [
        str(PYTHON), str(AUTO_PY),
        "--modo", modo,
        "--engine", engine,
        "--top", str(top),
        "--limit", "1",
    ]
    if dry_run:
        cmd.append("--dry-run")

    env = dict(os.environ, PYTHONUTF8="1")
    log(f"Iniciando anime_auto.py --modo {modo} (top={top})")

    try:
        # Timeout generoso: um recap longo renderizado no worker PC2 leva bem
        # mais que 30min. O cliente do worker (anime_worker_client) espera 4000s;
        # aqui damos folga extra pra não matar o job remoto no meio. Configurável
        # por ANIME_AUTO_TIMEOUT_S.
        _round_to = int(os.environ.get("ANIME_AUTO_TIMEOUT_S", "5400"))  # 90 min
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=_round_to,
            env=env,
        )
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        output = stdout + "\n" + stderr

        # Detectar sucesso vs falha
        has_final = ("final_anime_" in output) or ("PRONTO" in output) or ("SUCESSO" in output)
        has_error = ("ERROR" in output) or ("FALHA" in output) or ("erro" in output)

        if result.returncode == 0 and has_final:
            log("SUCESSO nesta rodada")
            return True, "success", output
        elif result.returncode == 0 and not has_error:
            log("Rodada completada (sem erro aparente)")
            return True, "success", output
        else:
            err_type = _detect_error_type(output)
            log(f"Falha detectada (tipo={err_type}, rc={result.returncode})")
            return False, err_type, output

    except subprocess.TimeoutExpired:
        log(f"TIMEOUT — anime_auto.py passou de {_round_to}s", "WARNING")
        return False, "pipeline_error", "timeout"
    except Exception as e:
        log(f"Exceção: {e}", "ERROR")
        return False, "unknown", str(e)


def worker_health_check():
    """Checa se o worker PC2 está online."""
    if not WORKER_HOST:
        return None
    try:
        import urllib.request
        url = f"http://{WORKER_HOST}:{WORKER_PORT}/health"
        with urllib.request.urlopen(url, timeout=2) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Anime Night Shift Driver")
    parser.add_argument("--modo", choices=["short", "deitado", "ambos"],
                        default="short", help="Modo de geração")
    parser.add_argument("--engine", choices=["local", "worker", "both"], default="both",
                       help="local=tudo aqui | worker=tudo no PC2 | both=short PC2 + deitado local")
    parser.add_argument("--top", type=int, default=5,
                        help="Quantos candidatos por rodada")
    parser.add_argument("--limit", type=int, default=1,
                        help="Quantos processar por rodada")
    parser.add_argument("--dry-run", action="store_true",
                        help="Testar sem renderizar")
    parser.add_argument("--max-runs", type=int, default=0,
                        help="Máximo de rodadas (0=infinito)")
    args = parser.parse_args()

    _write_pid()
    log(f"=== Anime Night Shift INICIADO (modo={args.modo}, engine={args.engine}, top={args.top}) ===")

    st = load_state()
    run_count = st.get("runs", 0)
    success_count = st.get("successes", 0)
    fail_count = st.get("failures", 0)
    consecutive_fails = st.get("consecutive_fails", 0)
    skipped = set(st.get("skipped_videos", []))

    # Se muitos erros consecutivos, dar mais tempo de cooldown
    max_consecutive = 5
    extra_cooldown = 0

    try:
        while True:
            run_count += 1
            if args.max_runs > 0 and run_count > args.max_runs:
                log(f"Limite de {args.max_runs} rodadas atingido. Encerrando.")
                break

            # Alternar modo se "ambos"
            if args.modo == "ambos":
                modo = "short" if (run_count % 2 == 1) else "deitado"
            else:
                modo = args.modo

            ok, err_type, output = run_anime_auto(modo, args.engine, args.top, dry_run=args.dry_run)

            # Atualizar estado
            st["runs"] = run_count
            st["last_run"] = datetime.now().isoformat()
            st["last_mode"] = modo
            st["last_error"] = err_type if not ok else None

            if ok:
                success_count += 1
                consecutive_fails = 0
                extra_cooldown = 0
            else:
                fail_count += 1
                consecutive_fails += 1
                # Cooldown progressivo: a cada 3 falhas consecutivas, dobra o tempo
                if consecutive_fails >= 3:
                    extra_cooldown = COOLDOWN.get(err_type, COOLDOWN["unknown"]) * (consecutive_fails // 3)
                if consecutive_fails >= max_consecutive:
                    log(f"ALERTA: {consecutive_fails} falhas consecutivas. Ajustando cooldown.", "WARNING")

            st["successes"] = success_count
            st["failures"] = fail_count
            st["consecutive_fails"] = consecutive_fails
            save_state(st)

            # Calcular cooldown
            base = COOLDOWN.get(err_type, COOLDOWN["unknown"])
            cooldown = base + extra_cooldown
            log(f"Descansando {cooldown}s antes da próxima rodada (tipo={err_type}, "
                f"sucessos={success_count}, falhas={fail_count})")
            time.sleep(cooldown)

            # Alternar modo se "ambos"
            if args.modo == "ambos":
                modo = "deitado" if modo == "short" else "short"

    except KeyboardInterrupt:
        log("Interrompido pelo usuário.")
    finally:
        log(f"=== Anime Night Shift ENCERRADO (rodadas={run_count}, "
            f"sucessos={success_count}, falhas={fail_count}) ===")
        try:
            PIDFILE.unlink(missing_ok=True)
        except Exception:
            pass


if __name__ == "__main__":
    main()
