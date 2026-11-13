"""
Lança bot no PC3 via schtasks (Windows Task Scheduler) — garantido sobreviver ao SSH.
"""
import paramiko
import time
import os
from scp import SCPClient

PC3_IP = "100.108.160.85"
PC3_USER = "Emerson-IA"
PC3_PASS = "Ssh@2026"

WRAPPER = r'''import sys, os, traceback
os.chdir("C:/projetos-navegador")
os.environ["PYTHONUTF8"] = "1"
sys.path.insert(0, "C:/projetos-navegador")
log = open("C:/projetos-navegador/bot_output.log", "w", encoding="utf-8", buffering=1)
sys.stdout = log
sys.stderr = log
print("=== BOT WRAPPER START ===", flush=True)
try:
    from engage_modules.main import main
    main()
except Exception as e:
    traceback.print_exc()
finally:
    print("=== BOT WRAPPER EXIT ===", flush=True)
    log.close()
'''

def main():
    print(f"Conectando em {PC3_USER}@{PC3_IP}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PC3_IP, username=PC3_USER, password=PC3_PASS, timeout=15)
    scp = SCPClient(ssh.get_transport(), socket_timeout=60)

    # Matar processos Python anteriores
    print("Matando processos Python existentes...")
    ssh.exec_command('powershell -c "Stop-Process -Name python -Force -ErrorAction SilentlyContinue"')
    time.sleep(2)

    # Upload wrapper
    tmp_py = os.path.join(os.environ.get("TEMP", "/tmp"), "_bot_wrapper.py")
    with open(tmp_py, "w", encoding="utf-8") as f:
        f.write(WRAPPER)
    scp.put(tmp_py, "C:/projetos-navegador/_bot_wrapper.py")
    scp.close()
    print("Wrapper enviado.")

    # Deletar task anterior se existe
    ssh.exec_command('schtasks /Delete /TN "MegaEngageBot" /F 2>$null')
    time.sleep(1)

    # Criar task que roda agora — usando schtasks via cmd
    # /SC ONCE /ST hora_atual /TR "python -u wrapper.py"
    from datetime import datetime
    # Pegar hora do PC3
    stdin_t, stdout_t, _ = ssh.exec_command('powershell -c "Get-Date -Format HH:mm"', timeout=10)
    remote_time = stdout_t.read().decode("utf-8", errors="replace").strip()
    print(f"Hora no PC3: {remote_time}")

    # Calcular 1 minuto no futuro pra dar tempo de criar
    h, m = map(int, remote_time.split(':'))
    m += 1
    if m >= 60:
        m = 0
        h = (h + 1) % 24
    run_time = f"{h:02d}:{m:02d}"
    print(f"Task agendada pra: {run_time}")

    create_cmd = (
        f'schtasks /Create /TN "MegaEngageBot" '
        f'/TR "C:\\projetos-navegador\\venv\\Scripts\\python.exe -u C:\\projetos-navegador\\_bot_wrapper.py" '
        f'/SC ONCE /ST {run_time} /F '
        f'/RU Emerson-IA /RP Ssh@2026'
    )
    stdin_c, stdout_c, stderr_c = ssh.exec_command(create_cmd, timeout=15)
    out_c = stdout_c.read().decode("utf-8", errors="replace").strip()
    err_c = stderr_c.read().decode("utf-8", errors="replace").strip()
    print(f"schtasks create: {out_c}")
    if err_c:
        print(f"schtasks err: {err_c}")

    # Alternativa: rodar imediatamente com /Run
    time.sleep(2)
    stdin_r, stdout_r, stderr_r = ssh.exec_command('schtasks /Run /TN "MegaEngageBot"', timeout=15)
    out_r = stdout_r.read().decode("utf-8", errors="replace").strip()
    err_r = stderr_r.read().decode("utf-8", errors="replace").strip()
    print(f"schtasks run: {out_r}")
    if err_r:
        print(f"schtasks run err: {err_r}")

    # Esperar 20s e verificar
    print("\nEsperando 20s...")
    time.sleep(20)

    # Checar processos
    stdin2, stdout2, stderr2 = ssh.exec_command(
        'powershell -c "Get-Process python -ErrorAction SilentlyContinue | Format-Table Id, CPU, WorkingSet64 -AutoSize"',
        timeout=10
    )
    proc_out = stdout2.read().decode("utf-8", errors="replace").strip()
    if proc_out:
        print(f"\nProcessos Python ativos:\n{proc_out}")
    else:
        print("\nNENHUM processo Python rodando!")

    # Ler log
    stdin3, stdout3, stderr3 = ssh.exec_command(
        'powershell -c "if (Test-Path C:\\projetos-navegador\\bot_output.log) { Get-Content C:\\projetos-navegador\\bot_output.log -Tail 30 } else { echo \'Log nao existe\' }"',
        timeout=10
    )
    log_out = stdout3.read().decode("utf-8", errors="replace").strip()
    print(f"\nLog do bot:\n{log_out}")

    ssh.close()
    os.unlink(tmp_py)

if __name__ == "__main__":
    main()
