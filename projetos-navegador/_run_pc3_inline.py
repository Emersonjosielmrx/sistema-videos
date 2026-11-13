"""
Roda o bot diretamente no PC3 via SSH (sem DETACHED_PROCESS)
pra capturar o traceback real da morte.
Timeout de 30s - se o bot viver 30s sem crash, está OK.
"""
import paramiko
import time
import os
import select
from scp import SCPClient

PC3_IP = "100.108.160.85"
PC3_USER = "Emerson-IA"
PC3_PASS = "Ssh@2026"

# Script que roda o bot inline (não detached) com flush imediato
RUN_INLINE = r'''
import sys
import os
import traceback

os.chdir("C:/projetos-navegador")
os.environ["PYTHONUTF8"] = "1"
sys.path.insert(0, "C:/projetos-navegador")

print("=== BOT STARTING ===", flush=True)

try:
    from engage_modules.main import main
    print("=== CALLING main() ===", flush=True)
    main()
except SystemExit as e:
    print(f"=== SystemExit: {e} ===", flush=True)
except KeyboardInterrupt:
    print("=== KeyboardInterrupt ===", flush=True)
except Exception as e:
    print(f"=== EXCEPTION: {type(e).__name__}: {e} ===", flush=True)
    traceback.print_exc()
    sys.stdout.flush()

print("=== BOT EXITED ===", flush=True)
'''

def main():
    print(f"Conectando em {PC3_USER}@{PC3_IP}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PC3_IP, username=PC3_USER, password=PC3_PASS, timeout=15)
    scp = SCPClient(ssh.get_transport(), socket_timeout=60)

    # Upload inline runner
    tmp = os.path.join(os.environ.get("TEMP", "/tmp"), "_run_inline.py")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(RUN_INLINE)

    scp.put(tmp, "C:/projetos-navegador/_run_inline.py")
    print("Script inline enviado.")
    scp.close()

    # Matar processos Python anteriores
    ssh.exec_command('powershell -c "Stop-Process -Name python -Force -ErrorAction SilentlyContinue"')
    time.sleep(2)

    # Executar inline (não detached) - captura tudo
    print("\n--- Executando bot inline (max 30s) ---\n")
    cmd = 'C:\\projetos-navegador\\venv\\Scripts\\python.exe -u C:\\projetos-navegador\\_run_inline.py'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=45)

    # Ler output com timeout
    result_lines = []
    start = time.time()
    channel = stdout.channel

    while time.time() - start < 35:
        if channel.exit_status_ready():
            # Processo terminou
            remaining = stdout.read().decode("utf-8", errors="replace")
            if remaining:
                result_lines.append(remaining)
            break

        if channel.recv_ready():
            data = channel.recv(4096).decode("utf-8", errors="replace")
            result_lines.append(data)
            print(data, end="", flush=True)

        time.sleep(0.5)
    else:
        # Timeout de 35s - bot está vivo!
        print("\n\n>>> BOT ESTÁ VIVO (rodou >30s sem crash) <<<")
        # Agora vamos matar esse e relançar como detached
        channel.close()

    # Capturar stderr
    err = stderr.read().decode("utf-8", errors="replace").strip()

    full_output = "".join(result_lines)

    # Salvar resultado
    result_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_run_result.txt")
    with open(result_file, "w", encoding="utf-8") as rf:
        rf.write("=== STDOUT ===\n")
        rf.write(full_output)
        rf.write("\n=== STDERR ===\n")
        rf.write(err)

    print(f"\n\nResultado salvo em: {result_file}")
    print(f"Exit status: {channel.recv_exit_status() if channel.exit_status_ready() else 'still running'}")

    ssh.close()
    os.unlink(tmp)

if __name__ == "__main__":
    main()
