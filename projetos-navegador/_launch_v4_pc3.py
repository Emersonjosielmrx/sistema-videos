"""
Lança bot no PC3 — envia um .bat e .ps1 e tenta ambas abordagens.
O truque é executar tudo via arquivo no disco, evitando escaping do SSH+PowerShell.
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

# PS1 que tenta wmic, se falhar tenta subprocess + DETACHED
LAUNCHER_PS1 = r'''
$ErrorActionPreference = "Continue"
$logFile = "C:\projetos-navegador\launcher_output.log"

"=== LAUNCHER START $(Get-Date) ===" | Out-File $logFile -Encoding UTF8

try {
    # Abordagem: Invoke-WmiMethod (PowerShell nativo, não precisa do wmic.exe)
    $result = Invoke-WmiMethod -Class Win32_Process -Name Create -ArgumentList "C:\projetos-navegador\venv\Scripts\python.exe -u C:\projetos-navegador\_bot_wrapper.py"
    "WMI ReturnValue=$($result.ReturnValue) PID=$($result.ProcessId)" | Out-File $logFile -Append -Encoding UTF8

    if ($result.ReturnValue -eq 0) {
        "SUCCESS: Bot lancado com PID $($result.ProcessId)" | Out-File $logFile -Append -Encoding UTF8
        Write-Output "PID=$($result.ProcessId)"
        exit 0
    }
} catch {
    "WMI FAILED: $_" | Out-File $logFile -Append -Encoding UTF8
}

# Fallback: Start-Process python.exe direto
try {
    $proc = Start-Process -FilePath "C:\projetos-navegador\venv\Scripts\python.exe" -ArgumentList @("-u", "C:\projetos-navegador\_bot_wrapper.py") -WorkingDirectory "C:\projetos-navegador" -WindowStyle Hidden -PassThru
    "Start-Process PID=$($proc.Id)" | Out-File $logFile -Append -Encoding UTF8
    Write-Output "PID=$($proc.Id)"
} catch {
    "Start-Process FAILED: $_" | Out-File $logFile -Append -Encoding UTF8
    Write-Output "FAILED"
}
'''

def main():
    print(f"Conectando em {PC3_USER}@{PC3_IP}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PC3_IP, username=PC3_USER, password=PC3_PASS, timeout=15)
    scp = SCPClient(ssh.get_transport(), socket_timeout=60)

    # Matar processos Python anteriores
    print("Matando processos Python existentes...")
    ssh.exec_command('powershell -c "Stop-Process -Name python* -Force -ErrorAction SilentlyContinue"')
    time.sleep(3)

    # Limpar logs
    ssh.exec_command('powershell -c "Remove-Item C:\\projetos-navegador\\bot_output.log, C:\\projetos-navegador\\launcher_output.log -Force -ErrorAction SilentlyContinue"')
    time.sleep(1)

    # Upload wrapper + launcher
    tmp_dir = os.environ.get("TEMP", "/tmp")

    tmp_py = os.path.join(tmp_dir, "_bot_wrapper.py")
    with open(tmp_py, "w", encoding="utf-8") as f:
        f.write(WRAPPER)
    scp.put(tmp_py, "C:/projetos-navegador/_bot_wrapper.py")

    tmp_ps1 = os.path.join(tmp_dir, "_launcher.ps1")
    with open(tmp_ps1, "w", encoding="utf-8") as f:
        f.write(LAUNCHER_PS1)
    scp.put(tmp_ps1, "C:/projetos-navegador/_launcher.ps1")
    scp.close()
    print("Wrapper + Launcher PS1 enviados.")

    # Executar o .ps1 (é um arquivo no disco, sem problemas de escaping)
    print("\nExecutando launcher.ps1...")
    stdin, stdout, stderr = ssh.exec_command(
        'powershell -ExecutionPolicy Bypass -File C:\\projetos-navegador\\_launcher.ps1',
        timeout=20
    )
    out = stdout.read().decode("utf-8", errors="replace").strip()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    print(f"Output: {out}")
    if err:
        print(f"Stderr: {err}")

    # Esperar 25s pro bot inicializar
    print("\nEsperando 25s...")
    time.sleep(25)

    # Checar processos
    stdin2, stdout2, _ = ssh.exec_command(
        'powershell -c "Get-Process python* -ErrorAction SilentlyContinue | Format-Table Id, ProcessName, CPU, WorkingSet64 -AutoSize"',
        timeout=10
    )
    proc_out = stdout2.read().decode("utf-8", errors="replace").strip()
    if proc_out:
        print(f"\nProcessos Python ativos:\n{proc_out}")
    else:
        print("\nNENHUM processo Python rodando!")

    # Ler launcher log
    stdin_l, stdout_l, _ = ssh.exec_command(
        'powershell -c "if (Test-Path C:\\projetos-navegador\\launcher_output.log) { Get-Content C:\\projetos-navegador\\launcher_output.log } else { Write-Output \'Launcher log nao existe\' }"',
        timeout=10
    )
    launcher_log = stdout_l.read().decode("utf-8", errors="replace").strip()
    print(f"\nLauncher log:\n{launcher_log}")

    # Ler bot log
    stdin3, stdout3, _ = ssh.exec_command(
        'powershell -c "if (Test-Path C:\\projetos-navegador\\bot_output.log) { Get-Content C:\\projetos-navegador\\bot_output.log -Tail 40 } else { Write-Output \'Bot log nao existe\' }"',
        timeout=10
    )
    log_out = stdout3.read().decode("utf-8", errors="replace").strip()
    print(f"\nBot log:\n{log_out}")

    ssh.close()
    os.unlink(tmp_py)
    os.unlink(tmp_ps1)
    print("\nFinalizado.")

if __name__ == "__main__":
    main()
