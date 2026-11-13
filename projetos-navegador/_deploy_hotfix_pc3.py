"""Deploy correções (account_health.py + worker.py) pro PC3 e reinicia bot."""
import paramiko, os, time, json
from scp import SCPClient

PC3_IP = "100.108.160.85"
PC3_USER = "Emerson-IA"
PC3_PASS = "Ssh@2026"

base = os.path.dirname(os.path.abspath(__file__))

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(PC3_IP, username=PC3_USER, password=PC3_PASS, timeout=15)
scp = SCPClient(ssh.get_transport(), socket_timeout=60)

# 1. Matar bot existente
print("1. Matando processos Python...")
ssh.exec_command('powershell -c "Stop-Process -Name python* -Force -ErrorAction SilentlyContinue"')
time.sleep(3)

# 2. Upload dos 2 arquivos corrigidos (precisa converter paths D: -> C:)
files_to_deploy = [
    ("engage_modules/account_health.py", "C:/projetos-navegador/engage_modules/account_health.py"),
    ("engage_modules/worker.py", "C:/projetos-navegador/engage_modules/worker.py"),
]

print("2. Enviando arquivos corrigidos...")
for local_rel, remote in files_to_deploy:
    local_path = os.path.join(base, local_rel)
    # Ler, substituir D: paths por C:, e enviar
    with open(local_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Path replacements pra PC3
    path_map = {
        "D:\\\\projetos-navegador": "C:\\\\projetos-navegador",
        "D:/projetos-navegador": "C:/projetos-navegador",
        "D:\\projetos-navegador": "C:\\projetos-navegador",
    }
    for old, new in path_map.items():
        content = content.replace(old, new)

    tmp = os.path.join(os.environ.get("TEMP", "/tmp"), os.path.basename(local_rel))
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(content)
    scp.put(tmp, remote)
    os.unlink(tmp)
    print(f"   OK: {local_rel} -> {remote}")

# 3. Limpar health data (resetar todos os cooldowns acumulados)
print("3. Resetando account_health.json (limpar cooldowns antigos)...")
reset_ps1 = r'''
$healthFile = "C:\projetos-navegador\data\account_health.json"
if (Test-Path $healthFile) {
    $health = Get-Content $healthFile -Raw | ConvertFrom-Json
    $props = $health | Get-Member -MemberType NoteProperty | Select-Object -ExpandProperty Name
    foreach ($acc in $props) {
        $health.$acc.consecutive_fails = 0
        $health.$acc.PSObject.Properties.Remove("cooldown_until")
    }
    $health | ConvertTo-Json -Depth 10 | Out-File $healthFile -Encoding UTF8
    Write-Output "Health resetado: $($props.Count) contas limpas"
} else {
    Write-Output "Health file nao existe (ok, sera criado)"
}
'''
tmp_ps1 = os.path.join(os.environ.get("TEMP", "/tmp"), "_reset_health.ps1")
with open(tmp_ps1, "w", encoding="utf-8") as f:
    f.write(reset_ps1)
scp.put(tmp_ps1, "C:/projetos-navegador/_reset_health.ps1")
_, stdout, stderr = ssh.exec_command(
    'powershell -ExecutionPolicy Bypass -File C:\\projetos-navegador\\_reset_health.ps1',
    timeout=10
)
print(f"   {stdout.read().decode('utf-8', errors='replace').strip()}")
os.unlink(tmp_ps1)

# 4. Limpar dead_accounts.txt (contas erroneamente marcadas como mortas por proxy errors)
print("4. Limpando dead_accounts.txt...")
ssh.exec_command('powershell -c "Remove-Item C:\\projetos-navegador\\dead_accounts.txt -Force -ErrorAction SilentlyContinue"')
time.sleep(1)

# 5. Relançar bot via wrapper + WMI
print("5. Relançando bot...")
scp.close()

# Limpar logs antigos
ssh.exec_command('powershell -c "Remove-Item C:\\projetos-navegador\\bot_output.log, C:\\projetos-navegador\\launcher_output.log -Force -ErrorAction SilentlyContinue"')
time.sleep(1)

# Upload wrapper (o mesmo que já funciona)
wrapper = r'''import sys, os, traceback
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
tmp_py = os.path.join(os.environ.get("TEMP", "/tmp"), "_bot_wrapper.py")
with open(tmp_py, "w", encoding="utf-8") as f:
    f.write(wrapper)
scp2 = SCPClient(ssh.get_transport(), socket_timeout=60)
scp2.put(tmp_py, "C:/projetos-navegador/_bot_wrapper.py")

# Launcher PS1 com WMI
launcher = r'''
$ErrorActionPreference = "Continue"
$logFile = "C:\projetos-navegador\launcher_output.log"
"=== LAUNCHER START $(Get-Date) ===" | Out-File $logFile -Encoding UTF8
try {
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
try {
    $proc = Start-Process -FilePath "C:\projetos-navegador\venv\Scripts\python.exe" -ArgumentList @("-u", "C:\projetos-navegador\_bot_wrapper.py") -WorkingDirectory "C:\projetos-navegador" -WindowStyle Hidden -PassThru
    "Start-Process PID=$($proc.Id)" | Out-File $logFile -Append -Encoding UTF8
    Write-Output "PID=$($proc.Id)"
} catch {
    "Start-Process FAILED: $_" | Out-File $logFile -Append -Encoding UTF8
    Write-Output "FAILED"
}
'''
tmp_ps1 = os.path.join(os.environ.get("TEMP", "/tmp"), "_launcher.ps1")
with open(tmp_ps1, "w", encoding="utf-8") as f:
    f.write(launcher)
scp2.put(tmp_ps1, "C:/projetos-navegador/_launcher.ps1")
scp2.close()
os.unlink(tmp_py)

_, stdout, stderr = ssh.exec_command(
    'powershell -ExecutionPolicy Bypass -File C:\\projetos-navegador\\_launcher.ps1',
    timeout=20
)
out = stdout.read().decode("utf-8", errors="replace").strip()
err = stderr.read().decode("utf-8", errors="replace").strip()
print(f"   Launch: {out}")
if err:
    print(f"   Stderr: {err}")
os.unlink(tmp_ps1)

# 6. Esperar e verificar
print("\n6. Esperando 30s pro bot inicializar...")
time.sleep(30)

_, stdout, _ = ssh.exec_command(
    'powershell -c "Get-Process python* -ErrorAction SilentlyContinue | Format-Table Id, ProcessName, CPU -AutoSize"',
    timeout=10
)
print(f"Processos: {stdout.read().decode('utf-8', errors='replace').strip()}")

_, stdout, _ = ssh.exec_command(
    'powershell -c "Get-Content C:\\projetos-navegador\\bot_output.log -Tail 20 -ErrorAction SilentlyContinue"',
    timeout=10
)
print(f"\nLog:\n{stdout.read().decode('utf-8', errors='replace').strip()}")

ssh.close()
print("\nDeploy + restart concluído!")
