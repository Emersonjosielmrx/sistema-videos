import paramiko
import time
from datetime import datetime

def check():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('100.108.160.85', username='Emerson-IA', password='<SEGREDO_REMOVIDO>', timeout=30)
    
    _, out, _ = ssh.exec_command('powershell -c "(Get-Process python* -EA SilentlyContinue).Count"', timeout=15)
    py = int(out.read().decode().strip() or 0)
    
    _, out, _ = ssh.exec_command('powershell -c "(Get-Process chrome* -EA SilentlyContinue).Count"', timeout=15)
    ch = int(out.read().decode().strip() or 0)
    
    _, out, _ = ssh.exec_command(r'powershell -c "(Select-String -Path C:\projetos-navegador\bot_output.log -Pattern \"OK \[L\]\" -EA SilentlyContinue).Count"', timeout=30)
    likes = int(out.read().decode().strip() or 0)
    
    _, out, _ = ssh.exec_command(r'powershell -c "(Select-String -Path C:\projetos-navegador\bot_output.log -Pattern \"Chrome morreu\" -EA SilentlyContinue).Count"', timeout=30)
    deaths = int(out.read().decode().strip() or 0)
    
    ssh.close()
    return py, ch, likes, deaths

print(f"[{datetime.now().strftime('%H:%M:%S')}] Monitor 1h iniciado")

inicio = time.time()
checks = []

for i in range(12):  # 12 checks x 5min = 60min
    try:
        py, ch, likes, deaths = check()
        elapsed = int((time.time() - inicio) / 60)
        checks.append((elapsed, py, ch, likes, deaths))
        status = "VIVO" if py >= 2 else "MORTO"
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Check {i+1}: {status} ({elapsed}min) | Py={py} Ch={ch} L={likes} Dead={deaths}")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Check {i+1}: ERRO - {str(e)[:60]}")
    
    if i < 11:
        time.sleep(300)  # 5 min

print(f"\n{'='*60}")
print("RESULTADO 1H")
print(f"{'='*60}")
if checks:
    final = checks[-1]
    print(f"Bot vivo no final: {'SIM' if final[1] >= 2 else 'NAO'}")
    print(f"Likes totais: {final[3]}")
    print(f"Chrome deaths: {final[4]}")
    print(f"Chrome final: {final[2]}")
    
    # Check if Chrome count grew out of control
    if final[2] > 40:
        print("[WARN] Chrome count > 40 = possivel leak/travamento")
