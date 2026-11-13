"""Espera 3 min e verifica se hotfix 3 reduziu erros."""
import paramiko, time
from collections import Counter

print("Aguardando 3 minutos...")
time.sleep(180)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("100.108.160.85", username="Emerson-IA", password="<SEGREDO_REMOVIDO>", timeout=15)

cmd = r'powershell -c "Get-Content C:\projetos-navegador\bot_output.log -Tail 100 -ErrorAction SilentlyContinue"'
_, stdout, _ = ssh.exec_command(cmd, timeout=15)
raw = stdout.read().decode("utf-8", errors="replace")
lines = raw.splitlines()

# Contar tipos de erro
context_destroyed = sum(1 for l in lines if "Context destroyed" in l or "Execution context was destroyed" in l)
navigation_to = sum(1 for l in lines if "Navigation to" in l and "ERRO" in l)
chrome_morreu = sum(1 for l in lines if "Chrome morreu" in l)
proxy_falhou = sum(1 for l in lines if "Proxy falhou" in l)
health_cooldown = sum(1 for l in lines if "[HEALTH]" in l and "cooldown" in l)
oks = sum(1 for l in lines if "OK [" in l)

print(f"\nULTIMAS 100 LINHAS:")
print(f"  OKs: {oks}")
print(f"  Context destroyed: {context_destroyed}")
print(f"  Navigation to: {navigation_to}")
print(f"  Chrome morreu: {chrome_morreu}")
print(f"  Proxy falhou (correto): {proxy_falhou}")
print(f"  Health cooldown (penaliza conta): {health_cooldown}")

# Verificar se "Context destroyed" agora é tratado como infra
context_lines = [l for l in lines if "Context destroyed" in l or "Execution context was destroyed" in l]
if context_lines:
    print(f"\n=== CONTEXT DESTROYED ({len(context_lines)}) ===")
    for l in context_lines[:3]:
        try:
            print(l.strip())
        except UnicodeEncodeError:
            print(l.encode("ascii", errors="replace").decode().strip())
    # Verificar se tem "Chrome morreu" logo depois
    chrome_apos = sum(1 for i, l in enumerate(lines) if "Context destroyed" in l and i+1 < len(lines) and "Chrome morreu" in lines[i+1])
    print(f"  Tratado como infra (Chrome morreu): {chrome_apos}/{len(context_lines)}")

print(f"\n=== ULTIMAS 10 LINHAS ===")
for l in lines[-10:]:
    try:
        print(l.strip())
    except UnicodeEncodeError:
        print(l.encode("ascii", errors="replace").decode().strip())

ssh.close()
