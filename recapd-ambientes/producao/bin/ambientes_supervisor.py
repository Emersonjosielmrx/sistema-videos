#!/usr/bin/env python
"""ambientes_supervisor.py — orquestra os 3 AMBIENTES do recap de anime.

REGRA PERMANENTE (definida pela dona — NÃO afrouxar sem ordem explícita):

  Ambiente 1  PROD  (produção/latest)  -> NUNCA é desligado de vez. É o worker
                                          padrão; sempre volta a rodar.
  Ambiente 2  BETA  (produção experimental) -> roda quando sobra recurso.
  Ambiente 3  TESTE (bancada de melhorias)  -> roda só pra validar mudança.

  Prioridade por RECURSO (RAM + CPU), reavaliada a cada ciclo:
    - Recurso OK        -> PROD roda. BETA/TESTE podem pegar um turno.
    - Recurso BAIXO     -> mata TESTE (3) primeiro; segura BETA (2); mantém PROD (1).
    - Recurso CRÍTICO   -> mata TESTE e BETA (3 e 2). Se há teste PENDENTE de
                           validação, PROD cede UM turno pro TESTE e volta a
                           rodar assim que o teste termina.

  A máquina mal aguarda 1 render pesado -> só 1 worker ATIVO por vez. Este
  supervisor decide QUEM roda, garante que o default é sempre o PROD, e mata
  os de menor prioridade quando o recurso aperta — com AVISO no log (nunca
  morre calado).

Independência: mede RAM/CPU por ctypes (Windows) sem depender de nenhuma
pasta hipercool. Só usa os arquivos do próprio projeto.

Uso:
  python ambientes_supervisor.py --status          # mostra estado e decisão
  python ambientes_supervisor.py --loop            # supervisiona continuamente
  python ambientes_supervisor.py --loop --once     # 1 ciclo só (pra cron)
"""
import argparse
import ctypes
import json
import logging
import os
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_DIR = Path(__file__).resolve().parent.parent
STATE_FILE = PROJECT_DIR / "workspace" / "ambientes_estado.json"
LOG_DIR = PROJECT_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "ambientes_supervisor.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("ambientes")

# ── Ambientes ─────────────────────────────────────────────────────────
# prioridade: menor número = mais importante (PROD nunca some).
PROD, BETA, TESTE = "prod", "beta", "teste"
PRIORIDADE = {PROD: 1, BETA: 2, TESTE: 3}

# Cada ambiente é uma worktree própria (isolamento de código por versão),
# todas dentro da MESMA pasta-mãe (D:\recapd-ambientes\):
#   producao\ (PROD) | beta\ (BETA) | experimental\ (TESTE)
# Se a worktree não existir, o supervisor ignora aquele ambiente
# (PROD sempre existe = a própria pasta onde este script roda).
_MAE = PROJECT_DIR.parent  # D:\recapd-ambientes
AMBIENTE_DIR = {
    PROD:  PROJECT_DIR,             # ...\producao
    BETA:  _MAE / "beta",
    TESTE: _MAE / "experimental",
}

# ── Limiares de recurso (env-configuráveis) ─────────────────────────────
def _envf(name, default):
    try:
        return float(os.environ.get(name, str(default)))
    except (ValueError, TypeError):
        return default

# RAM livre (MB): acima de OK = folga; abaixo de CRIT = crítico.
RAM_OK_MB   = _envf("AMB_RAM_OK_MB", 3000)    # >= 3GB livre -> tudo pode rodar
RAM_CRIT_MB = _envf("AMB_RAM_CRIT_MB", 1200)  # <  1.2GB livre -> crítico
# CPU (%): abaixo de OK = folga; acima de CRIT = crítico.
CPU_OK_PCT   = _envf("AMB_CPU_OK_PCT", 70)    # <= 70% -> folga
CPU_CRIT_PCT = _envf("AMB_CPU_CRIT_PCT", 92)  # >  92% -> crítico


# ── Medição de recurso (ctypes puro, sem dependência externa) ───────────
class _MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", wintypes.DWORD),
        ("dwMemoryLoad", wintypes.DWORD),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def free_ram_mb():
    try:
        st = _MEMORYSTATUSEX()
        st.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st)):
            return st.ullAvailPhys / (1024 * 1024)
    except Exception:
        pass
    return None


def _get_system_times():
    try:
        idle = wintypes.FILETIME()
        kern = wintypes.FILETIME()
        usr = wintypes.FILETIME()
        if not ctypes.windll.kernel32.GetSystemTimes(
            ctypes.byref(idle), ctypes.byref(kern), ctypes.byref(usr)
        ):
            return None
        def _v(ft):
            return (ft.dwHighDateTime << 32) | ft.dwLowDateTime
        return _v(idle), _v(kern), _v(usr)
    except Exception:
        return None


def cpu_load_pct(sample_s=0.5):
    a = _get_system_times()
    if a is None:
        return None
    time.sleep(sample_s)
    b = _get_system_times()
    if b is None:
        return None
    idle_d = b[0] - a[0]
    total_d = (b[1] - a[1]) + (b[2] - a[2])  # kernel já inclui idle
    if total_d <= 0:
        return None
    return max(0.0, min(100.0, (1.0 - idle_d / total_d) * 100.0))


def nivel_recurso():
    """Classifica o recurso atual em: 'ok', 'baixo' ou 'critico'."""
    ram = free_ram_mb()
    cpu = cpu_load_pct()
    # Se não conseguir medir, assume 'baixo' (conservador: protege o PROD).
    if ram is None and cpu is None:
        return "baixo", ram, cpu
    ram_crit = ram is not None and ram < RAM_CRIT_MB
    cpu_crit = cpu is not None and cpu > CPU_CRIT_PCT
    if ram_crit or cpu_crit:
        return "critico", ram, cpu
    ram_ok = ram is None or ram >= RAM_OK_MB
    cpu_ok = cpu is None or cpu <= CPU_OK_PCT
    if ram_ok and cpu_ok:
        return "ok", ram, cpu
    return "baixo", ram, cpu


# ── Estado persistente ──────────────────────────────────────────────────
def carregar_estado():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "workers": {},          # ambiente -> pid (quem está rodando)
        "teste_pendente": False,  # há melhoria aguardando validação no TESTE?
        "atualizado": None,
    }


def salvar_estado(st):
    st["atualizado"] = time.strftime("%Y-%m-%d %H:%M:%S")
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")


# ── Controle de processo por ambiente ────────────────────────────────────
def _pid_vivo(pid):
    if not pid:
        return False
    try:
        # tasklist é o jeito mais confiável no Windows sem libs externas.
        r = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH", "/FO", "CSV"],
            capture_output=True, text=True, timeout=15,
        )
        return str(pid) in r.stdout
    except Exception:
        return False


def matar(ambiente, st):
    pid = st["workers"].get(ambiente)
    if not pid:
        return
    if _pid_vivo(pid):
        log.warning(f"[recurso] AVISO: encerrando ambiente {ambiente.upper()} "
                    f"(pid {pid}) pra liberar recurso — prioridade "
                    f"{PRIORIDADE[ambiente]}. Nada é morto sem este aviso.")
        try:
            # /T mata a árvore (ffmpeg filhos). /F força.
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                           capture_output=True, timeout=20)
        except Exception as e:
            log.error(f"[recurso] falha ao encerrar {ambiente}: {e}")
    st["workers"].pop(ambiente, None)


def worker_ativo(st):
    """Retorna (ambiente, pid) do worker vivo, ou (None, None). Limpa mortos."""
    for amb in (PROD, BETA, TESTE):
        pid = st["workers"].get(amb)
        if pid and _pid_vivo(pid):
            return amb, pid
        if pid:  # registrado mas morreu -> limpa
            st["workers"].pop(amb, None)
    return None, None


# ── DECISÃO: quem deve rodar agora ───────────────────────────────────────
def decidir(nivel, st):
    """Aplica a REGRA PERMANENTE e devolve o ambiente que DEVE estar ativo.

    Só 1 worker ativo por vez (a máquina não aguarda 2 renders pesados).
    """
    teste_pendente = st.get("teste_pendente", False)

    if nivel == "ok":
        # Folga: PROD é o padrão. (BETA/TESTE pegam turno via --promover,
        # decisão manual/cron; o default seguro é sempre PROD rodando.)
        return PROD

    if nivel == "baixo":
        # Mata TESTE primeiro; segura BETA; mantém PROD.
        matar(TESTE, st)
        # BETA só continua se JÁ estava rodando; não inicia novo sob pressão.
        amb, _ = worker_ativo(st)
        if amb == BETA:
            return BETA
        return PROD

    # nivel == "critico": mata TESTE e BETA. PROD manda.
    matar(TESTE, st)
    matar(BETA, st)
    if teste_pendente:
        # Exceção da regra: cede UM turno pro TESTE validar a melhoria, e
        # volta pro PROD assim que o teste terminar (visto no próximo ciclo,
        # quando teste_pendente já terá sido baixado pela conclusão).
        log.info("[recurso] crítico, mas há TESTE pendente — PROD cede 1 turno "
                 "pro TESTE validar; volta a rodar quando o teste acabar.")
        return TESTE
    return PROD


def _iniciar(ambiente, st):
    """Inicia o worker do ambiente se a pasta existir e nada estiver ativo.

    O worker do anime é o anime_night_shift.py (driver noturno que roda
    anime_auto.py em loop). NÃO é o night-shift-driver.py, que é do
    the-meek-cat (mangá/hipercool).
    """
    d = AMBIENTE_DIR[ambiente]
    driver = d / "bin" / "anime_night_shift.py"
    py = d / "venv" / "Scripts" / "python.exe"
    if not d.exists() or not driver.exists():
        if ambiente != PROD:
            log.info(f"[start] ambiente {ambiente.upper()} sem worktree ainda "
                     f"({d}) — ignorando.")
        return
    if not py.exists():
        py = AMBIENTE_DIR[PROD] / "venv" / "Scripts" / "python.exe"  # fallback venv PROD
    log.info(f"[start] iniciando ambiente {ambiente.upper()} ({d})")
    try:
        env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
                   AMBIENTE=ambiente)
        p = subprocess.Popen(
            [str(py), str(driver), "--modo", "deitado", "--top", "2"],
            cwd=str(d), env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
        st["workers"][ambiente] = p.pid
    except Exception as e:
        log.error(f"[start] falha ao iniciar {ambiente}: {e}")


def aplicar(nivel, ram, cpu, iniciar=True):
    st = carregar_estado()
    alvo = decidir(nivel, st)
    ativo, pid = worker_ativo(st)

    ram_s = f"{ram:.0f}MB" if ram is not None else "?"
    cpu_s = f"{cpu:.0f}%" if cpu is not None else "?"
    log.info(f"[ciclo] recurso={nivel} (RAM livre {ram_s}, CPU {cpu_s}) "
             f"| ativo={ativo or '-'} | alvo={alvo.upper()}")

    if ativo and ativo != alvo:
        # o worker ativo tem prioridade MENOR que o alvo? troca.
        if PRIORIDADE[ativo] > PRIORIDADE[alvo]:
            log.info(f"[ciclo] trocando {ativo.upper()} -> {alvo.upper()} "
                     f"(alvo tem prioridade maior)")
            matar(ativo, st)
            ativo = None

    if iniciar and not ativo:
        _iniciar(alvo, st)

    salvar_estado(st)
    return st


def cmd_status():
    nivel, ram, cpu = nivel_recurso()
    st = carregar_estado()
    ativo, pid = worker_ativo(st)
    alvo = decidir(nivel, dict(st))  # cópia: decidir pode matar; status não age
    ram_s = f"{ram:.0f}MB" if ram is not None else "?"
    cpu_s = f"{cpu:.0f}%" if cpu is not None else "?"
    print("=" * 56)
    print(f"  RECURSO : {nivel.upper()}  (RAM livre {ram_s} | CPU {cpu_s})")
    print(f"  LIMIARES: RAM ok>={RAM_OK_MB:.0f} crit<{RAM_CRIT_MB:.0f} | "
          f"CPU ok<={CPU_OK_PCT:.0f} crit>{CPU_CRIT_PCT:.0f}")
    print(f"  ATIVO   : {(ativo or '-').upper()}  (pid {pid or '-'})")
    print(f"  ALVO    : {alvo.upper()}  (quem DEVE rodar agora)")
    print(f"  TESTE pendente: {st.get('teste_pendente', False)}")
    for amb in (PROD, BETA, TESTE):
        d = AMBIENTE_DIR[amb]
        existe = "ok" if d.exists() else "SEM worktree"
        print(f"    {PRIORIDADE[amb]}. {amb.upper():5} -> {existe}  ({d})")
    print("=" * 56)


def main():
    ap = argparse.ArgumentParser(description="Supervisor dos 3 ambientes do recap de anime")
    ap.add_argument("--status", action="store_true", help="mostra estado e decisão (não age)")
    ap.add_argument("--loop", action="store_true", help="supervisiona continuamente")
    ap.add_argument("--once", action="store_true", help="com --loop: roda 1 ciclo só (pra cron)")
    ap.add_argument("--intervalo", type=int, default=30, help="segundos entre ciclos (--loop)")
    ap.add_argument("--sem-iniciar", action="store_true",
                    help="só mata quem deve morrer; não inicia worker (útil pra teste)")
    ap.add_argument("--marcar-teste-pendente", action="store_true",
                    help="marca que há melhoria aguardando validação no TESTE")
    ap.add_argument("--limpar-teste-pendente", action="store_true",
                    help="baixa a flag de teste pendente (melhoria validada)")
    args = ap.parse_args()

    if args.marcar_teste_pendente or args.limpar_teste_pendente:
        st = carregar_estado()
        st["teste_pendente"] = bool(args.marcar_teste_pendente)
        salvar_estado(st)
        print(f"teste_pendente = {st['teste_pendente']}")
        return

    if args.status:
        cmd_status()
        return

    if args.loop:
        log.info(f"[supervisor] iniciando loop (intervalo {args.intervalo}s). "
                 f"Regra permanente: PROD nunca para; sob pressão mata TESTE, "
                 f"depois BETA; PROD é o default.")
        while True:
            try:
                nivel, ram, cpu = nivel_recurso()
                aplicar(nivel, ram, cpu, iniciar=not args.sem_iniciar)
            except Exception as e:
                log.error(f"[supervisor] erro no ciclo: {e}")
            if args.once:
                break
            time.sleep(args.intervalo)
        return

    cmd_status()


if __name__ == "__main__":
    main()
