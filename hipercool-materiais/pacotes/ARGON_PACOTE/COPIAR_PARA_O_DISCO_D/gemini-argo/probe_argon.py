#!/usr/bin/env python3
r"""probe_argon.py - manda um "oi" em cada conta do Argon NA HORA que ela volta, e grava no log se
aquela conta esta funcionando (dona 29/10: "so precisa ser na hora que aquela conta voltar").

NAO fica rodando de X em X min. A tarefa ProbeArgon tem UM gatilho de uma vez, no horario de volta
da proxima conta (campo sem_cota_ate da contas_argon.json). Ao disparar:
  1. sonda SO as contas que voltaram desde a ultima checagem (sem_cota_ate passou agora) com um "oi";
  2. grava em probe_argon.log se aquela conta respondeu;
  3. reagenda a propria tarefa pro proximo horario de volta (ou +60 min se nao houver, pra recapturar
     contas que sairam de cota depois).
Conta que nunca saiu de cota nao e sondada (nao "voltou"). --agora ignora o relogio e sonda as prontas.
Log: D:\gemini-argo\probe_argon.log
"""
import io
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, r"D:\gemini-argo")
import gemini_http  # noqa: E402

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CONTAS = Path(r"D:\gemini-argo\contas_argon.json")
STATE = Path(r"D:\gemini-argo\probe_argon_estado.json")
LOG = Path(r"D:\gemini-argo\probe_argon.log")
LOCK = Path(os.environ.get("TEMP", r"D:\gemini-argo")) / "probe_argon.lock"
TAREFA = "ProbeArgon"
HEARTBEAT_MIN = 60  # sem volta agendada, recheca em 1 h (nao e polling de 10 min)


def carregar(p, padrao):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def logar(linha):
    with LOG.open("a", encoding="utf-8") as f:
        f.write(linha + "\n")
    print(linha)


def reagendar(quando):
    """Poe o unico gatilho da tarefa ProbeArgon no horario 'quando' (datetime)."""
    iso = quando.strftime("%Y-%m-%dT%H:%M:%S")
    ps = (f"$t=New-ScheduledTaskTrigger -Once -At '{iso}'; "
          f"Set-ScheduledTask -TaskName '{TAREFA}' -Trigger $t | Out-Null")
    try:
        subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                       capture_output=True, timeout=60,
                       creationflags=0x08000000 if sys.platform == "win32" else 0)
        print(f"  reagendado para {iso}")
    except Exception as e:  # noqa: BLE001
        print(f"  FALHA ao reagendar: {e}")


def travar():
    try:
        if LOCK.exists():
            try:
                pid = int(LOCK.read_text())
            except (ValueError, OSError):
                pid = None
            if pid:
                import ctypes
                h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
                if h:
                    ctypes.windll.kernel32.CloseHandle(h)
                    return False
        LOCK.write_text(str(os.getpid()))
        return True
    except OSError:
        return True


def main():
    agora = datetime.now()
    manual = "--agora" in sys.argv
    if not manual and not travar():
        print("outro probe_argon rodando; saindo")
        return
    dados = carregar(CONTAS, {"contas": []})
    estado = carregar(STATE, {})
    contas = [c for c in dados.get("contas", []) if not c.get("bloqueada")]
    ult = estado.get("ultima_checagem")  # ISO da ultima vez que rodamos

    def apelido(c):
        return c.get("apelido") or c.get("email", "?").split("@")[0]

    # Contas que VOLTARAM desde a ultima checagem: sem_cota_ate no passado agora, mas depois da ultima
    # checagem (ou seja, cruzaram o horario de volta nesta janela). 1a execucao (sem ult): nao sonda nada.
    due = []
    if manual:
        due = [c for c in contas if not (c.get("sem_cota_ate") and c["sem_cota_ate"] > agora.isoformat())]
    elif ult:
        for c in contas:
            sca = c.get("sem_cota_ate")
            if sca and ult < sca <= agora.isoformat():
                due.append(c)

    if due:
        print(f"[{agora:%H:%M:%S}] {len(due)} conta(s) voltaram; sondando")
        for c in due:
            ap = apelido(c)
            t0 = time.time()
            try:
                r = gemini_http.perguntar("oi", conta=ap, tentativas=1)
                dt = time.time() - t0
                if r and r.strip():
                    logar(f"{agora:%d/%m %H:%M} {ap} OK {dt:.0f}s | {r.strip()[:50]!r}")
                else:
                    logar(f"{agora:%d/%m %H:%M} {ap} FALHA (vazia) {dt:.0f}s")
            except Exception as e:  # noqa: BLE001
                logar(f"{agora:%d/%m %H:%M} {ap} FALHA ({type(e).__name__}: {str(e)[:60]}) {time.time()-t0:.0f}s")
            time.sleep(3)
    else:
        print(f"[{agora:%H:%M:%S}] nenhuma conta voltou nesta janela")

    estado["ultima_checagem"] = datetime.now().isoformat(timespec="seconds")
    STATE.write_text(json.dumps(estado, indent=1, ensure_ascii=False), encoding="utf-8")

    # Proximo horario de volta (a conta mais proxima de voltar); senao, heartbeat de 1 h.
    futuras = sorted(c["sem_cota_ate"] for c in contas
                     if c.get("sem_cota_ate") and c["sem_cota_ate"] > datetime.now().isoformat())
    if futuras:
        prox = datetime.fromisoformat(futuras[0]) + timedelta(seconds=30)
        teto = datetime.now() + timedelta(minutes=HEARTBEAT_MIN)
        prox = min(prox, teto)
    else:
        prox = datetime.now() + timedelta(minutes=HEARTBEAT_MIN)
    if not manual:
        reagendar(prox)


if __name__ == "__main__":
    main()
