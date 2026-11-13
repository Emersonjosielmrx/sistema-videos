"""Envia e roda um .ps1 de diagnostico no PC3."""
import paramiko, os, time
from scp import SCPClient

DIAG_PS1 = r'''
$ErrorActionPreference = "Continue"
$out = ""

$out += "=== PROCESSOS PYTHON ===`n"
Get-Process python* -ErrorAction SilentlyContinue | ForEach-Object {
    $out += "PID=$($_.Id) Name=$($_.ProcessName) CPU=$($_.CPU) WS=$(($_.WorkingSet64/1MB).ToString('F1'))MB Path=$($_.Path)`n"
}

$out += "`n=== COMMANDLINES ===`n"
Get-WmiObject Win32_Process -Filter "Name like 'python%'" -ErrorAction SilentlyContinue | ForEach-Object {
    $out += "PID=$($_.ProcessId) CMD=$($_.CommandLine)`n"
}

$out += "`n=== LOG FILES ===`n"
Get-ChildItem "C:\projetos-navegador\*.log" -ErrorAction SilentlyContinue | ForEach-Object {
    $out += "$($_.Name) Size=$($_.Length) Modified=$($_.LastWriteTime)`n"
}

$out += "`n=== bot_output.log ===`n"
if (Test-Path "C:\projetos-navegador\bot_output.log") {
    $content = Get-Content "C:\projetos-navegador\bot_output.log" -Tail 30 -ErrorAction SilentlyContinue
    if ($content) { $out += ($content -join "`n") + "`n" }
    else { $out += "(empty file)`n" }
} else { $out += "(not found)`n" }

$out += "`n=== launcher_output.log ===`n"
if (Test-Path "C:\projetos-navegador\launcher_output.log") {
    $content = Get-Content "C:\projetos-navegador\launcher_output.log" -ErrorAction SilentlyContinue
    if ($content) { $out += ($content -join "`n") + "`n" }
    else { $out += "(empty file)`n" }
} else { $out += "(not found)`n" }

$out += "`n=== engage.log ===`n"
if (Test-Path "C:\projetos-navegador\engage.log") {
    $content = Get-Content "C:\projetos-navegador\engage.log" -Tail 30 -ErrorAction SilentlyContinue
    if ($content) { $out += ($content -join "`n") + "`n" }
    else { $out += "(empty file)`n" }
} else { $out += "(not found)`n" }

$out += "`n=== stats.json ===`n"
if (Test-Path "C:\projetos-navegador\engage_stats.json") {
    $content = Get-Content "C:\projetos-navegador\engage_stats.json" -Raw -ErrorAction SilentlyContinue
    $out += $content + "`n"
} else { $out += "(not found)`n" }

$out | Out-File "C:\projetos-navegador\_diag_result2.txt" -Encoding UTF8
Write-Output "DIAG DONE"
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('100.108.160.85', username='Emerson-IA', password='<SEGREDO_REMOVIDO>', timeout=15)
scp = SCPClient(ssh.get_transport(), socket_timeout=60)

tmp = os.path.join(os.environ.get("TEMP", "/tmp"), "_diag2.ps1")
with open(tmp, "w", encoding="utf-8") as f:
    f.write(DIAG_PS1)
scp.put(tmp, "C:/projetos-navegador/_diag2.ps1")
scp.close()

_, stdout, stderr = ssh.exec_command(
    'powershell -ExecutionPolicy Bypass -File C:\\projetos-navegador\\_diag2.ps1',
    timeout=20
)
print("PS1 output:", stdout.read().decode("utf-8", errors="replace").strip())
err = stderr.read().decode("utf-8", errors="replace").strip()
if err:
    print("PS1 error:", err)

# Baixar resultado
time.sleep(1)
scp2 = SCPClient(ssh.get_transport(), socket_timeout=60)
local_result = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_diag_result2.txt")
scp2.get("C:/projetos-navegador/_diag_result2.txt", local_result)
scp2.close()

with open(local_result, "r", encoding="utf-8") as f:
    print(f.read())

ssh.close()
os.unlink(tmp)
