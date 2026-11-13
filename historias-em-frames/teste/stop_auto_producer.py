"""stop_auto_producer.py — Para o daemon e TODOS os processos filhos.

Mata: auto_producer.py (daemon) + story_pipeline.py (filhos em andamento).
Remove o lock file. Deixa o PC limpo de processos de producao.

Robusto: usa o PID do lock (taskkill /T mata a arvore) + varredura wmic com
retry (wmic as vezes retorna vazio na 1a chamada). NAO toca em hiper-pipeline,
anime-pipeline nem outros processos python do PC.
"""
import os
import subprocess
import time
from pathlib import Path

# Tudo relativo a ESTA pista (raiz/prod/beta/teste). A mesma copia funciona em
# qualquer uma sem editar nada — igual ao auto_producer.py.
PROJECT_DIR = Path(__file__).resolve().parent
LOCK_FILE = PROJECT_DIR / "workspace" / ".auto_producer.lock"
LOG_FILE = PROJECT_DIR / "logs" / "auto-producer.md"
NEEDLES = ("auto_producer.py", "story_pipeline.py")
# ISOLAMENTO: so mata processos DESTA pista (cuja linha de comando aponta pra
# dentro do proprio diretorio). Assim parar 'teste' nunca derruba 'prod'/'beta'.
PISTA_TAG = (str(PROJECT_DIR).lower() + os.sep)
SELF_PID = os.getpid()


def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"- [{ts}] {msg}"
    print(line)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def find_pids(needle, retries=3):
    """PIDs de python/pythonw cuja linha de comando contem needle.
    wmic as vezes retorna vazio na 1a chamada — por isso o retry."""
    for attempt in range(retries):
        pids = []
        try:
            out = subprocess.run(
                ["wmic", "process", "where", "name like '%python%'",
                 "get", "ProcessId,CommandLine", "/format:csv"],
                capture_output=True, text=True, timeout=30,
            ).stdout or ""
            for line in out.splitlines():
                if "stop_auto_producer.py" in line:
                    continue  # nao matar a si mesmo
                # ISOLAMENTO: so processos cuja cmdline aponta pra ESTA pista
                if PISTA_TAG not in line.lower():
                    continue
                if needle in line:
                    parts = line.strip().rsplit(",", 1)
                    if len(parts) == 2 and parts[1].isdigit():
                        pid = int(parts[1])
                        if pid != SELF_PID:
                            pids.append(pid)
            if pids or out.strip():
                return pids
        except Exception as e:
            print(f"WARN wmic (tent {attempt+1}): {e}")
        time.sleep(1)
    return []


def kill_tree(pid):
    """Mata o processo e toda a arvore de filhos (/T)."""
    try:
        subprocess.run(["taskkill", "/PID", str(pid), "/F", "/T"],
                       capture_output=True, timeout=15)
        return True
    except Exception:
        return False


def read_lock_pid():
    try:
        return int(LOCK_FILE.read_text(encoding="utf-8").strip())
    except Exception:
        return None


def main():
    killed = set()

    # 1) Mata a arvore a partir do PID do lock (pega daemon + filho story_pipeline)
    lock_pid = read_lock_pid()
    if lock_pid:
        if kill_tree(lock_pid):
            killed.add(lock_pid)

    # 2) Varredura por needle (pega orfaos e o par shim/real do venv)
    for needle in NEEDLES:
        for pid in find_pids(needle):
            if pid not in killed:
                kill_tree(pid)
                killed.add(pid)

    time.sleep(2)

    # 3) Segunda passada — garante que nada sobreviveu
    sobrou = []
    for needle in NEEDLES:
        sobrou += find_pids(needle)
    for pid in sobrou:
        kill_tree(pid)

    # 4) Remove lock
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except Exception:
        pass

    log(f"STOP: {len(killed)} processos finalizados, lock removido. PC limpo.")
    print(f"\n=== {len(killed)} processos parados. Producao DESLIGADA. ===")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERRO no stop: {e}")
    # sempre sai 0 pro .bat nao acusar erro
    raise SystemExit(0)