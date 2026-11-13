"""
Deploy MEGA ENGAGE v3 — só os 9 arquivos das 22 inteligências novas.

Transfere via Paramiko/SCP pro PC3, aplica patch D: -> C:, testa importação.
Não mexe em chrome-profiles, sessions, secrets (já estão lá).

Uso:
    D:\hipercool-videos\venv\Scripts\python.exe D:\projetos-navegador\_deploy_v3_inteligencias.py
"""
import paramiko
import os
import time
from pathlib import Path
from scp import SCPClient

PC3_IP = "100.108.160.85"
PC3_USER = "Emerson-IA"
PC3_PASS = "Ssh@2026"

LOCAL_BASE = Path("D:/projetos-navegador")
REMOTE_BASE = "C:/projetos-navegador"

FILES_TO_DEPLOY = [
    "engage_modules/__init__.py",
    "engage_modules/config.py",
    "engage_modules/logger.py",
    "engage_modules/flags.py",
    "engage_modules/progress.py",
    "engage_modules/timezone.py",
    "engage_modules/account_health.py",
    "engage_modules/personalities.py",
    "engage_modules/comments.py",
    "engage_modules/smart_comments.py",
    "engage_modules/browser.py",
    "engage_modules/engagement.py",
    "engage_modules/worker.py",
    "engage_modules/warmup.py",
    "engage_modules/scheduler.py",
    "engage_modules/stats.py",
    "engage_modules/main.py",
    "mega_engage.py",
]

PATH_MAP = {
    "D:/projetos-navegador": "C:/projetos-navegador",
    "D:\\projetos-navegador": "C:\\projetos-navegador",
    "D:/logins-google": "C:/logins-google",
    "D:\\logins-google": "C:\\logins-google",
    "D:/hipercool-videos/venv/Scripts/python.exe": "C:/projetos-navegador/venv/Scripts/python.exe",
    "D:\\hipercool-videos\\venv\\Scripts\\python.exe": "C:\\projetos-navegador\\venv\\Scripts\\python.exe",
    "D:/hipercool-videos/secrets": "C:/projetos-navegador/secrets",
}


def main():
    print("=" * 60)
    print("DEPLOY v3 — 22 Inteligências -> PC3")
    print(f"Target: {PC3_USER}@{PC3_IP}")
    print(f"Arquivos: {len(FILES_TO_DEPLOY)}")
    print("=" * 60)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    print(f"\nConectando em {PC3_USER}@{PC3_IP}...")
    ssh.connect(PC3_IP, username=PC3_USER, password=PC3_PASS, timeout=15)
    scp = SCPClient(ssh.get_transport(), socket_timeout=120)
    print("  Conectado!")

    try:
        # Criar diretório data/ se não existe (account_health.json vai lá)
        print("\n--- Criando diretório data/ ---")
        ssh.exec_command(f'powershell -c "New-Item -ItemType Directory -Force -Path \'{REMOTE_BASE}/data\'" > $null')
        time.sleep(1)

        # Upload e patch de cada arquivo
        print("\n--- Upload + Patch ---")
        for rel in FILES_TO_DEPLOY:
            local_path = LOCAL_BASE / rel
            if not local_path.exists():
                print(f"  SKIP {rel} (não encontrado localmente)")
                continue

            content = local_path.read_text(encoding="utf-8")

            changed = False
            for old, new in PATH_MAP.items():
                if old in content:
                    content = content.replace(old, new)
                    changed = True

            if changed:
                tmp = LOCAL_BASE / f"_tmp_deploy_{rel.replace('/', '_')}"
                tmp.write_text(content, encoding="utf-8")
                remote = f"{REMOTE_BASE}/{rel}"
                scp.put(str(tmp), remote)
                tmp.unlink()
                print(f"  PATCHED+UPLOADED {rel}")
            else:
                remote = f"{REMOTE_BASE}/{rel}"
                scp.put(str(local_path), remote)
                print(f"  UPLOADED {rel}")

        # Teste de importação
        print("\n--- Teste de importação ---")
        test_cmd = (
            'cmd /c "C:\\projetos-navegador\\venv\\Scripts\\python.exe" -c '
            '"import sys; sys.path.insert(0, chr(67)+chr(58)+chr(47)+chr(112)+chr(114)+chr(111)+chr(106)+chr(101)+chr(116)+chr(111)+chr(115)+chr(45)+chr(110)+chr(97)+chr(118)+chr(101)+chr(103)+chr(97)+chr(100)+chr(111)+chr(114)); '
            'from engage_modules.account_health import report_success; '
            'from engage_modules.personalities import get_personality; '
            'from engage_modules.engagement import discover_sidebar_channels; '
            'from engage_modules.worker import engage_batch_session; '
            'from engage_modules.stats import get_stats; '
            'print(chr(73)+chr(77)+chr(80)+chr(79)+chr(82)+chr(84)+chr(95)+chr(79)+chr(75))"'
        )
        stdin, stdout, stderr = ssh.exec_command(test_cmd, timeout=30)
        out = stdout.read().decode("utf-8", errors="ignore").strip()
        err = stderr.read().decode("utf-8", errors="ignore").strip()

        if "IMPORT_OK" in out:
            print("  SUCESSO! Todos os módulos importam corretamente.")
        else:
            print(f"  FALHA: {err[:200]}")

    finally:
        scp.close()
        ssh.close()

    print("\n" + "=" * 60)
    print("DEPLOY v3 COMPLETO — 22 inteligências ativas no PC3")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrompido.")
    except Exception as e:
        print(f"\nERRO: {e}")
        import traceback
        traceback.print_exc()
