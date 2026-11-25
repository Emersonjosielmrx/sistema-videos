"""Vigia do painel :8790 (24/11/2026). O painel_controlador travou 2x em 23/11: processo vivo, 0% CPU, 4-16 MB, sem
responder nem arquivo estático; depois de reiniciar pela tarefa subiram 2 cópias e a porta nem abriu. Com python.exe
e saída num arquivo ele sobe normal. Aqui: GET /status.html com prazo; sem resposta 2x seguidas = mata TODAS as cópias
e sobe UMA (python.exe escondido, saída em logs\\painel_saida.log / painel_erro.log). Chamado pelo vigia_geral
(SUBVIGIAS "painel", 10 min). PAINEL_SEM_VIGIA=1 desliga.

    python vigia_painel.py            # 1 volta
    python vigia_painel.py --simular  # só diz o que faria
"""
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
LOGS = BASE / "logs"
PY = r"D:\veo\venv\Scripts\python.exe"
URL = "http://127.0.0.1:8790/status.html"
SEM_JANELA = 0x08000000
SIMULAR = "--simular" in sys.argv


def log(msg):
    with open(LOGS / "vigia_painel.log", "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%d/%m %H:%M:%S')}] {msg}\n")
    if sys.stdout:
        print(msg, flush=True)


def responde(prazo=25):
    try:
        with urllib.request.urlopen(URL, timeout=prazo) as r:
            return r.status == 200
    except Exception:  # noqa: BLE001
        return False


def copias():
    ps = ("Get-CimInstance Win32_Process | ? { $_.CommandLine -match 'painel_controlador\\.py' -and "
          "$_.CommandLine -notmatch 'vigia_painel' } | % { $_.ProcessId }")
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=90,
                         creationflags=SEM_JANELA).stdout
    return [int(x) for x in out.split() if x.strip().isdigit()]


def religar(motivo):
    pids = copias()
    log(f"painel sem resposta ({motivo}); cópias vivas: {pids} -> religando 1")
    if SIMULAR:
        return
    subprocess.run(["schtasks", "/End", "/TN", "PainelVideos"], capture_output=True, creationflags=SEM_JANELA)
    for pid in pids:
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, creationflags=SEM_JANELA)
    time.sleep(3)
    out = open(LOGS / "painel_saida.log", "a", encoding="utf-8")
    err = open(LOGS / "painel_erro.log", "a", encoding="utf-8")
    subprocess.Popen([PY, str(BASE / "painel_controlador.py")], cwd=str(BASE), stdout=out, stderr=err,
                     creationflags=SEM_JANELA | 0x01000000, close_fds=True)  # fora do job de quem chamou
    for _ in range(24):
        time.sleep(5)
        if responde(10):
            log("painel voltou")
            return
    log("painel NÃO voltou em 2 min")
    try:
        sys.path.insert(0, str(BASE))
        import avisos
        avisos.enviar("Painel :8790 travou e não voltou sozinho (vigia_painel). Ver logs\\painel_erro.log.",
                      "vigia-painel", importante=True)
    except Exception:  # noqa: BLE001
        pass


def main():
    if os.environ.get("PAINEL_SEM_VIGIA") == "1":
        return
    if responde():
        return
    time.sleep(20)  # 1 lentidão passageira não religa
    if responde():
        return
    religar("2 tentativas de 25 s")


if __name__ == "__main__":
    main()
