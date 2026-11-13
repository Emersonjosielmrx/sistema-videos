"""
Lança o bot no PC3 como processo de fundo que sobrevive ao SSH.
Usa Start-Process do PowerShell (funcional no shell remoto).
"""
import paramiko
import time
import os
from scp import SCPClient

PC3_IP = "100.108.160.85"
PC3_USER = "Emerson-IA"
PC3_PASS = "Ssh@2026"

# Wrapper script simples — roda no PC3 como background
WRAPPER = r'''
import sys, os, traceback

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

    # Upload wrapper
    tmp = os.path.join(os.environ.get("TEMP", "/tmp"), "_bot_wrapper.py")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(WRAPPER)
    scp.put(tmp, "C:/projetos-navegador/_bot_wrapper.py")
    print("Wrapper enviado.")
    scp.close()

    # Lançar via Start-Process (PowerShell nativo — sobrevive SSH)
    print("Lançando bot via Start-Process...")
    launch_cmd = (
        'powershell -c "'
        'Start-Process -FilePath C:\\projetos-navegador\\venv\\Scripts\\python.exe '
        '-ArgumentList \'-u\', \'C:\\projetos-navegador\\_bot_wrapper.py\' '
        '-WorkingDirectory C:\\projetos-navegador '
        '-WindowStyle Hidden '
        '-PassThru | Select-Object -ExpandProperty Id'
        '"'
    )
    stdin, stdout, stderr = ssh.exec_command(launch_cmd, timeout=15)
    pid = stdout.read().decode("utf-8", errors="replace").strip()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    print(f"PID do bot: {pid}")
    if err:
        print(f"Erro: {err}")

    # Esperar 15s e verificar
    print("\nEsperando 15s pra verificar...")
    time.sleep(15)

    # Checar se processo está vivo
    stdin2, stdout2, stderr2 = ssh.exec_command(
        'powershell -c "Get-Process python -ErrorAction SilentlyContinue | Format-Table Id, CPU, WorkingSet64, StartTime -AutoSize"',
        timeout=10
    )
    proc_out = stdout2.read().decode("utf-8", errors="replace").strip()
    if proc_out:
        print(f"Processos Python ativos:\n{proc_out}")
    else:
        print("NENHUM processo Python rodando!")

    # Ler log
    stdin3, stdout3, stderr3 = ssh.exec_command(
        'powershell -c "if (Test-Path C:\\projetos-navegador\\bot_output.log) { Get-Content C:\\projetos-navegador\\bot_output.log -Tail 20 } else { echo \'Log nao existe\' }"',
        timeout=10
    )
    log_out = stdout3.read().decode("utf-8", errors="replace").strip()
    print(f"\nLog do bot:\n{log_out}")

    ssh.close()
    os.unlink(tmp)

if __name__ == "__main__":
    main()
