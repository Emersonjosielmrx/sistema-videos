"""
Lança bot no PC3 via .bat intermediário (evita hell de escaping PowerShell remoto).
"""
import paramiko
import time
import os
from scp import SCPClient

PC3_IP = "100.108.160.85"
PC3_USER = "Emerson-IA"
PC3_PASS = "Ssh@2026"

# Wrapper Python (roda no PC3)
WRAPPER = r'''import sys, os, traceback
os.chdir("C:/projetos-navegador")
os.environ["PYTHONUTF8"] = "1"
sys.path.insert(0, "C:/projetos-navegador")
log = open("C:/projetos-navegador/bot_output.log", "a", encoding="utf-8", buffering=1)
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

# BAT simples que roda o wrapper
BAT_CONTENT = r'''@echo off
set PYTHONUTF8=1
C:\projetos-navegador\venv\Scripts\python.exe -u C:\projetos-navegador\_bot_wrapper.py
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
    time.sleep(3)

    # Limpar log anterior
    ssh.exec_command('powershell -c "Remove-Item C:\\projetos-navegador\\bot_output.log -Force -ErrorAction SilentlyContinue"')
    time.sleep(1)

    # Upload wrapper Python
    tmp_py = os.path.join(os.environ.get("TEMP", "/tmp"), "_bot_wrapper.py")
    with open(tmp_py, "w", encoding="utf-8") as f:
        f.write(WRAPPER)
    scp.put(tmp_py, "C:/projetos-navegador/_bot_wrapper.py")

    # Upload BAT
    tmp_bat = os.path.join(os.environ.get("TEMP", "/tmp"), "_run_bot.bat")
    with open(tmp_bat, "w", encoding="utf-8") as f:
        f.write(BAT_CONTENT)
    scp.put(tmp_bat, "C:/projetos-navegador/_run_bot.bat")
    scp.close()

    print("Arquivos enviados. Lançando via Start-Process...")

    # Start-Process no BAT (sem ArgumentList = sem problema de escaping)
    launch_cmd = 'powershell -c "Start-Process -FilePath C:\\projetos-navegador\\_run_bot.bat -WorkingDirectory C:\\projetos-navegador -WindowStyle Hidden"'
    stdin, stdout, stderr = ssh.exec_command(launch_cmd, timeout=15)
    out = stdout.read().decode("utf-8", errors="replace").strip()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    if out:
        print(f"Output: {out}")
    if err:
        print(f"Erro: {err}")
    else:
        print("Start-Process OK (sem erro)")

    # Esperar 20s
    print("\nEsperando 20s pra verificar se está vivo...")
    time.sleep(20)

    # Checar processo
    stdin2, stdout2, stderr2 = ssh.exec_command(
        'powershell -c "Get-Process python -ErrorAction SilentlyContinue | Format-Table Id, CPU, WorkingSet64 -AutoSize"',
        timeout=10
    )
    proc_out = stdout2.read().decode("utf-8", errors="replace").strip()
    if proc_out:
        print(f"Processos Python ativos:\n{proc_out}")
    else:
        print("NENHUM processo Python rodando!")

    # Ler log
    stdin3, stdout3, stderr3 = ssh.exec_command(
        'powershell -c "if (Test-Path C:\\projetos-navegador\\bot_output.log) { Get-Content C:\\projetos-navegador\\bot_output.log -Tail 30 } else { echo \'Log nao existe\' }"',
        timeout=10
    )
    log_out = stdout3.read().decode("utf-8", errors="replace").strip()
    print(f"\nLog do bot (ultimas 30 linhas):\n{log_out}")

    ssh.close()
    os.unlink(tmp_py)
    os.unlink(tmp_bat)

if __name__ == "__main__":
    main()
