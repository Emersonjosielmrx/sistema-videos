"""
Lança o bot no PC3 como processo de fundo via nohup/Start-Process no PowerShell.
Redireciona stdout/stderr pra arquivo de log.
"""
import paramiko
import time
import os
from scp import SCPClient

PC3_IP = "100.108.160.85"
PC3_USER = "Emerson-IA"
PC3_PASS = "Ssh@2026"

LAUNCHER_SCRIPT = r'''
import subprocess
import sys
import os

os.chdir("C:/projetos-navegador")
env = os.environ.copy()
env["PYTHONUTF8"] = "1"

log_out = open("C:/projetos-navegador/bot_output.log", "w", encoding="utf-8")

proc = subprocess.Popen(
    ["C:/projetos-navegador/venv/Scripts/python.exe", "-u", "mega_engage.py"],
    cwd="C:/projetos-navegador",
    stdout=log_out,
    stderr=subprocess.STDOUT,
    env=env,
    creationflags=0x00000008 | 0x00000200,  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
)

print(f"PID={proc.pid}")
'''

def main():
    print(f"Conectando em {PC3_USER}@{PC3_IP}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PC3_IP, username=PC3_USER, password=PC3_PASS, timeout=15)
    scp = SCPClient(ssh.get_transport(), socket_timeout=60)

    # Matar qualquer Python existente primeiro
    print("Matando processes Python existentes...")
    ssh.exec_command('powershell -c "Stop-Process -Name python -Force -ErrorAction SilentlyContinue"')
    time.sleep(2)

    # Upload launcher
    tmp = os.path.join(os.environ.get("TEMP", "/tmp"), "_launch_bot.py")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(LAUNCHER_SCRIPT)

    scp.put(tmp, "C:/projetos-navegador/_launch_bot.py")
    print("Launcher enviado.")

    # Executar launcher (PowerShell syntax - set env var then run)
    cmd = 'powershell -c "$env:PYTHONUTF8=\'1\'; C:\\projetos-navegador\\venv\\Scripts\\python.exe C:\\projetos-navegador\\_launch_bot.py"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    out = stdout.read().decode("utf-8", errors="replace").strip()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    print(f"Launcher output: {out}")
    if err:
        print(f"Launcher stderr: {err}")

    # Esperar um pouco e checar se está vivo
    print("\nEsperando 10s pra verificar...")
    time.sleep(10)

    # Checar processo
    stdin2, stdout2, stderr2 = ssh.exec_command('powershell -c "Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, CPU, WorkingSet64 | Format-Table -AutoSize"', timeout=15)
    proc_out = stdout2.read().decode("utf-8", errors="replace").strip()
    print(f"Processos Python no PC3:\n{proc_out}" if proc_out else "Nenhum processo Python rodando!")

    # Ler primeiras linhas do log
    stdin3, stdout3, stderr3 = ssh.exec_command('powershell -c "if (Test-Path C:\\projetos-navegador\\bot_output.log) { Get-Content C:\\projetos-navegador\\bot_output.log -Tail 30 } else { echo \'Log nao encontrado\' }"', timeout=15)
    log_out = stdout3.read().decode("utf-8", errors="replace").strip()
    print(f"\nLog do bot (ultimas 30 linhas):\n{log_out}")

    scp.close()
    ssh.close()
    os.unlink(tmp)

if __name__ == "__main__":
    main()
