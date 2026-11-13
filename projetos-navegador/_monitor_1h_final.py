"""Monitor 1h final - validação de estabilidade MEGA ENGAGE v3"""
import paramiko
import time
from datetime import datetime

def check_bot():
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

print(f"[{datetime.now().strftime('%H:%M:%S')}] Monitor 1h final iniciado")
print("Objetivo: validar estabilidade antes de reportar pra usuaria")

start_time = time.time()
checks = []

for i in range(12):  # 12 checks x 5min = 60min
    try:
        py, ch, likes, deaths = check_bot()
        elapsed_min = int((time.time() - start_time) / 60)
        checks.append((elapsed_min, py, ch, likes, deaths))

        status = "VIVO" if py >= 2 else "MORTO"
        rate = round((likes / elapsed_min) * 60, 1) if elapsed_min > 0 else 0

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Check {i+1}/12: {status} | Py={py} Ch={ch} | L={likes} (~{rate}/h) | Dead={deaths} | {elapsed_min}min")

        if py < 2:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] BOT MORREU - abortando monitor")
            break

    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Check {i+1}/12: ERRO - {str(e)[:60]}")

    if i < 11:
        time.sleep(300)  # 5 min

print(f"\n{'='*60}")
print("RESULTADO 1H FINAL")
print(f"{'='*60}")

if checks:
    final = checks[-1]
    elapsed_total = final[0]

    print(f"Tempo monitorado: {elapsed_total} min")
    print(f"Bot vivo no final: {'SIM' if final[1] >= 2 else 'NAO'}")
    print(f"Likes totais: {final[3]}")
    print(f"Chrome deaths: {final[4]}")
    print(f"Python procs final: {final[1]}")
    print(f"Chrome procs final: {final[2]}")

    if elapsed_total > 0:
        rate = round((final[3] / elapsed_total) * 60, 1)
        print(f"Taxa: ~{rate} likes/hora")

    # Success criteria
    success = (
        final[1] >= 2 and  # Bot alive
        final[3] > 30 and  # Reasonable production
        final[2] < 40      # Chrome not leaking
    )

    if success:
        print("\n[SUCCESS] Bot estavel e produtivo")
        print("Pronto pra reportar pra usuaria")
    else:
        print(f"\n[PARTIAL] Bot funciona mas com issues:")
        if final[2] >= 40:
            print(f"  - Chrome acumulando ({final[2]} procs)")
        if final[3] <= 30:
            print(f"  - Producao baixa ({final[3]} likes em {elapsed_total}min)")

print("\nMonitor finalizado.")
