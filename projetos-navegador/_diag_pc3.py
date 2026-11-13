"""
Diagnóstico remoto: envia um script pro PC3 que tenta importar
e rodar o bot, capturando qualquer traceback.
"""
import paramiko
import tempfile
import time
from scp import SCPClient

PC3_IP = "100.108.160.85"
PC3_USER = "Emerson-IA"
PC3_PASS = "Ssh@2026"

DIAG_SCRIPT = r'''
import sys
import traceback

print("=== DIAG START ===")
print(f"Python: {sys.version}")
print(f"Executable: {sys.executable}")

# 1. Testar imports
try:
    sys.path.insert(0, "C:/projetos-navegador/shared")
    sys.path.insert(0, "C:/projetos-navegador")
    import os
    os.chdir("C:/projetos-navegador")
    print(f"CWD: {os.getcwd()}")

    print("\n--- Testando imports ---")
    from engage_modules.config import load_config, BASE_DIR
    print(f"  config OK, BASE_DIR={BASE_DIR}")

    from engage_modules.logger import log
    print("  logger OK")

    from engage_modules.flags import check_flags
    print("  flags OK")

    from engage_modules.progress import load_progress
    print("  progress OK")

    from engage_modules.browser import launch_chrome
    print("  browser OK")

    from engage_modules.engagement import simulate_watch
    print("  engagement OK")

    from engage_modules.worker import engage_batch_session
    print("  worker OK")

    from engage_modules.scheduler import run_batch
    print("  scheduler OK")

    from engage_modules.main import main
    print("  main OK")

    print("\n--- Verificando arquivos ---")
    from engage_modules.config import VIDEOS_FILE
    print(f"  VIDEOS_FILE={VIDEOS_FILE}, exists={VIDEOS_FILE.exists()}")

    cfg_file = BASE_DIR / "engage_config.json"
    print(f"  config_file={cfg_file}, exists={cfg_file.exists()}")

    from pathlib import Path
    shared = Path("C:/projetos-navegador/shared")
    print(f"  shared/={shared}, exists={shared.exists()}")
    gs = shared / "google_session.py"
    print(f"  google_session.py={gs}, exists={gs.exists()}")

    secrets = BASE_DIR / "secrets" / "gemini_keys.json"
    print(f"  gemini_keys={secrets}, exists={secrets.exists()}")

    logins = Path("C:/logins-google")
    print(f"  logins-google={logins}, exists={logins.exists()}")
    if logins.exists():
        subdirs = list(logins.iterdir())
        print(f"    {len(subdirs)} profiles")

    # 2. Verificar playwright
    print("\n--- Playwright ---")
    try:
        from playwright.sync_api import sync_playwright
        print("  playwright import OK")
    except Exception as e:
        print(f"  playwright FALHOU: {e}")

    # 3. Tentar carregar config
    print("\n--- Config ---")
    cfg = load_config()
    print(f"  mode={cfg.get('mode')}, workers={cfg.get('workers')}, paused={cfg.get('paused')}")

    # 4. Checar proxy list
    print("\n--- Proxy ---")
    try:
        from engage_modules.browser import health_check_proxies
        import engage_modules.browser as bmod
        health_check_proxies()
        hp = getattr(bmod, '_healthy_proxies', None)
        print(f"  proxies saudaveis: {len(hp) if hp else 0}")
    except Exception as e:
        print(f"  proxy check falhou: {e}")

    print("\n=== DIAG OK ===")

except Exception as e:
    print(f"\n=== DIAG FALHOU ===")
    traceback.print_exc()
'''

def main():
    print(f"Conectando em {PC3_USER}@{PC3_IP}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PC3_IP, username=PC3_USER, password=PC3_PASS, timeout=15)
    scp = SCPClient(ssh.get_transport(), socket_timeout=60)

    # Upload do script de diagnóstico
    import os
    tmp = os.path.join(os.environ.get("TEMP", "/tmp"), "_remote_diag.py")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(DIAG_SCRIPT)

    scp.put(tmp, "C:/projetos-navegador/_remote_diag.py")
    print("Script de diagnóstico enviado.")

    # Executar
    print("\n--- Executando diagnóstico ---\n")
    cmd = '"C:\\projetos-navegador\\venv\\Scripts\\python.exe" "C:\\projetos-navegador\\_remote_diag.py"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)

    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")

    result_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_diag_result.txt")
    with open(result_file, "w", encoding="utf-8") as rf:
        rf.write("=== STDOUT ===\n")
        rf.write(out)
        rf.write("\n=== STDERR ===\n")
        rf.write(err)

    print(f"Resultado salvo em: {result_file}")
    print(f"STDOUT len={len(out)}, STDERR len={len(err)}")

    scp.close()
    ssh.close()
    os.unlink(tmp)

if __name__ == "__main__":
    main()
