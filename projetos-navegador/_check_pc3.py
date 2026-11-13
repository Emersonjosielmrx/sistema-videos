"""Diagnostica o bot rodando no PC3 — checa processos, logs, etc."""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('100.108.160.85', username='Emerson-IA', password='<SEGREDO_REMOVIDO>', timeout=15)

checks = [
    ("Processos python", 'powershell -c "Get-Process python* -ErrorAction SilentlyContinue | Format-Table Id, ProcessName, CPU, WS -AutoSize"'),
    ("Path PID 14940", 'powershell -c "(Get-Process -Id 14940 -ErrorAction SilentlyContinue).Path"'),
    ("Path PID 17084", 'powershell -c "(Get-Process -Id 17084 -ErrorAction SilentlyContinue).Path"'),
    ("bot_output.log", 'powershell -c "if(Test-Path C:\\projetos-navegador\\bot_output.log){Get-Content C:\\projetos-navegador\\bot_output.log -Tail 20}else{\'NENHUM\'}"'),
    ("launcher_output.log", 'powershell -c "if(Test-Path C:\\projetos-navegador\\launcher_output.log){Get-Content C:\\projetos-navegador\\launcher_output.log}else{\'NENHUM\'}"'),
    ("engage.log", 'powershell -c "if(Test-Path C:\\projetos-navegador\\engage.log){Get-Content C:\\projetos-navegador\\engage.log -Tail 20}else{\'NENHUM\'}"'),
    ("Arquivos .log", 'powershell -c "Get-ChildItem C:\\projetos-navegador\\*.log | Select-Object Name, Length, LastWriteTime"'),
    ("Pasta logs/", 'powershell -c "if(Test-Path C:\\projetos-navegador\\logs){Get-ChildItem C:\\projetos-navegador\\logs\\*.log | Select-Object Name, Length | Format-Table}else{\'NENHUM\'}"'),
]

for label, cmd in checks:
    try:
        _, stdout, stderr = ssh.exec_command(cmd, timeout=8)
        out = stdout.read().decode("utf-8", errors="replace").strip()
        err = stderr.read().decode("utf-8", errors="replace").strip()
        print(f"\n=== {label} ===")
        print(out if out else "(vazio)")
        if err:
            print(f"ERR: {err}")
    except Exception as e:
        print(f"\n=== {label} === TIMEOUT/ERR: {e}")

ssh.close()
