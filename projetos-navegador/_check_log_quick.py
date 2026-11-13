import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("100.108.160.85", username="Emerson-IA", password="<SEGREDO_REMOVIDO>", timeout=15)
_, stdout, _ = ssh.exec_command(
    r'powershell -c "Get-Content C:\projetos-navegador\bot_output.log -Tail 40 -ErrorAction SilentlyContinue"',
    timeout=10
)
raw = stdout.read().decode("utf-8", errors="replace")
for line in raw.splitlines():
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode("ascii", errors="replace").decode())
ssh.close()
