#!/usr/bin/env python3
"""anime_worker_loop.py — loop infinito no PC2 (worker autonomy).
Roda tudo local: discover + pipeline + cleanup.
"""
import os, sys, time, subprocess, json
from pathlib import Path

PROJECT = Path(r"C:/recapd-e-animes")
LOG = PROJECT / "workspace" / "anime_worker_loop.log"
STATE = PROJECT / "workspace" / "anime_worker_loop_state.json"

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"{ts} {msg}"
    print(line)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def load_state():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {"runs": 0, "successes": 0, "failures": 0, "last_error": None}

def save_state(s):
    STATE.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")

def run_one():
    env = dict(os.environ, PYTHONUTF8="1", HF_HOME=r"D:\.cache\huggingface")
    python = str(PROJECT / "venv" / "Scripts" / "python.exe")
    cmd = [
        python, str(PROJECT / "bin" / "anime_auto.py"),
        "--modo", "short",
        "--top", "5",
        "--limit", "1",
        "--engine", "local",
    ]
    log(f"[loop] cmd: {' '.join(cmd)}")
    r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=900)
    return r

def main():
    st = load_state()
    log(f"[loop] INICIADO. runs={st['runs']} ok={st['successes']} fail={st['failures']}")

    while True:
        r = run_one()
        st["runs"] += 1
        out = (r.stdout + "\n" + r.stderr).lower()

        if r.returncode == 0 and ("pronto" in out or "sucesso" in out or "worker ok" in out or "final_anime" in out):
            st["successes"] += 1
            st["last_error"] = None
            save_state(st)
            log(f"[loop] OK! Cooldown 30s.")
            time.sleep(30)
        elif "429" in out or "quota" in out:
            st["failures"] += 1
            st["last_error"] = "quota_429"
            save_state(st)
            log(f"[loop] 429 — aguardando 5min.")
            time.sleep(300)
        elif "nenhum candidato" in out:
            st["failures"] += 1
            st["last_error"] = "no_candidates"
            save_state(st)
            log(f"[loop] Sem candidatos — aguardando 3min.")
            time.sleep(180)
        elif "sem transcri" in out or "no transcript" in out:
            st["failures"] += 1
            st["last_error"] = "no_transcript"
            save_state(st)
            log(f"[loop] Sem transcricao — aguardando 2min.")
            time.sleep(120)
        else:
            st["failures"] += 1
            st["last_error"] = f"rc={r.returncode}"
            save_state(st)
            log(f"[loop] ERRO rc={r.returncode}. Stdout: {r.stdout[:300]}")
            time.sleep(120)

if __name__ == "__main__":
    main()
