"""Baixa worker.py e account_health.py do PC3 pra inspeção."""
import paramiko, os
from scp import SCPClient

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('100.108.160.85', username='Emerson-IA', password='<SEGREDO_REMOVIDO>', timeout=15)
scp = SCPClient(ssh.get_transport(), socket_timeout=60)

base = os.path.dirname(os.path.abspath(__file__))
scp.get("C:/projetos-navegador/engage_modules/worker.py", os.path.join(base, "_pc3_worker.py"))
scp.get("C:/projetos-navegador/engage_modules/account_health.py", os.path.join(base, "_pc3_account_health.py"))
scp.close()
ssh.close()
print("Arquivos baixados.")
