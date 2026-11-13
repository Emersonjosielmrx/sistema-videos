import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("100.108.160.85", username="Emerson-IA", password="<SEGREDO_REMOVIDO>", timeout=15)

# Verificar patterns no worker.py
cmd = r'powershell -c "Select-String -Path C:\projetos-navegador\engage_modules\worker.py -Pattern ''Navigation to'',''ERR_FAILED'',''ERR_NAME_NOT_RESOLVED'',''200'' -SimpleMatch | ForEach-Object { $_.LineNumber.ToString() + '': '' + $_.Line.Trim() }"'
_, stdout, _ = ssh.exec_command(cmd, timeout=10)
raw = stdout.read().decode("utf-8", errors="replace")
print("=== Patterns no worker.py do PC3 ===")
for line in raw.splitlines():
    try:
        print(line.strip())
    except UnicodeEncodeError:
        print(line.encode("ascii", errors="replace").decode().strip())

ssh.close()
