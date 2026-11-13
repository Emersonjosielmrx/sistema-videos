import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("100.108.160.85", username="Emerson-IA", password="<SEGREDO_REMOVIDO>", timeout=15)

cmd = r'powershell -c "Get-Content C:\projetos-navegador\engage_modules\worker.py -Encoding UTF8 | Select-String ''is_proxy_error''"'
_, stdout, _ = ssh.exec_command(cmd, timeout=10)
raw = stdout.read().decode("utf-8", errors="replace")
print("is_proxy_error lines:")
for line in raw.splitlines():
    try:
        print(line.strip())
    except UnicodeEncodeError:
        print(line.encode("ascii", errors="replace").decode().strip())

print()
cmd2 = r'powershell -c "Get-Content C:\projetos-navegador\engage_modules\worker.py -Encoding UTF8 | Select-String ''err_msg''"'
_, stdout2, _ = ssh.exec_command(cmd2, timeout=10)
raw2 = stdout2.read().decode("utf-8", errors="replace")
print("err_msg lines:")
for line in raw2.splitlines():
    try:
        print(line.strip())
    except UnicodeEncodeError:
        print(line.encode("ascii", errors="replace").decode().strip())

ssh.close()
