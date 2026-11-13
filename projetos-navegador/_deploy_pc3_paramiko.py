"""
Deploy projetos-navegador para PC3 (100.108.160.85) via SSH com senha.

Transfere código + chrome-profiles + sessions + secrets, aplica patches D: -> C:,
instala Python venv e testa.

Uso:
    python D:/projetos-navegador/_deploy_pc3_paramiko.py
"""

import paramiko
import sys
import os
import time
from pathlib import Path
from scp import SCPClient

PC3_IP = "100.108.160.85"
PC3_USER = "Emerson-IA"
PC3_PASS = "Ssh@2026"

# Mapeamento de caminhos D: (PC1) -> C: (PC3)
PATH_MAP = {
    "D:/projetos-navegador": "C:/projetos-navegador",
    "D:\\projetos-navegador": "C:\\projetos-navegador",
    "D:/logins-google": "C:/logins-google",
    "D:\\logins-google": "C:\\logins-google",
    "D:/hipercool-videos/venv/Scripts/python.exe": "C:/projetos-navegador/venv/Scripts/python.exe",
    "D:\\hipercool-videos\\venv\\Scripts\\python.exe": "C:\\projetos-navegador\\venv\\Scripts\\python.exe",
    "D:/hipercool-videos/secrets": "C:/projetos-navegador/secrets",
}

# Arquivos que precisam de patch de caminhos (relativos a D:/projetos-navegador)
FILES_TO_PATCH = [
    "mega_engage.py",
    "engage_server.py",
    "engage_modules/config.py",
    "engage_modules/browser.py",
    "engage_modules/main.py",
    "engage_modules/scheduler.py",
    "engage_modules/smart_comments.py",
    "engage_modules/stats.py",
    "engage_modules/warmup.py",
    "engage_modules/worker.py",
    "shared/google_session.py",
    "shared/chrome_profile.py",
    "build_painel.py",
    "create_template.py",
    "discover_channels.py",
    "scan_new_channels.py",
    "orchestrator.py",
    "add_new_accounts.py",
    "youtube_engage.py",
    "youtube_engage_batch2.py",
    "youtube_engage_retry.py",
    "auto-refresh-sessoes/session_health_check.py",
    "RODAR_ENGAGE.bat",
    "_supervisor_engage.bat",
    "run_painel_server.bat",
]


class PC3Connection:
    """Gerencia conexão SSH + SCP pro PC3."""

    def __init__(self):
        self.ssh = None
        self.scp = None

    def __enter__(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Conectando em {PC3_USER}@{PC3_IP}...")
        self.ssh.connect(PC3_IP, username=PC3_USER, password=PC3_PASS, timeout=15)
        self.scp = SCPClient(self.ssh.get_transport(), socket_timeout=300)
        print("  Conectado!")
        return self

    def __exit__(self, *args):
        if self.scp:
            self.scp.close()
        if self.ssh:
            self.ssh.close()

    def exec(self, cmd, print_output=True):
        """Executa comando e retorna (stdout, stderr, returncode)."""
        if print_output:
            print(f"  CMD> {cmd}")
        stdin, stdout, stderr = self.ssh.exec_command(cmd, timeout=60)
        out = stdout.read().decode('utf-8', errors='ignore').strip()
        err = stderr.read().decode('utf-8', errors='ignore').strip()
        rc = stdout.channel.recv_exit_status()
        if print_output and out:
            print(f"    {out}")
        if err and rc != 0:
            print(f"    STDERR: {err}")
        return out, err, rc

    def mkdir(self, path):
        """Cria diretório (recursivo, não falha se existir)."""
        self.exec(f'powershell -c "New-Item -ItemType Directory -Force -Path \'{path}\'" > $null', print_output=False)

    def upload(self, local, remote):
        """Upload via SCP."""
        print(f"  SCP> {local} -> {remote}")
        self.scp.put(local, remote, recursive=True)


def step1_check_disk(conn):
    """Verifica espaço em disco."""
    print("\n=== STEP 1: Verificando espaço em disco ===")
    out, _, rc = conn.exec('powershell -c "(Get-PSDrive C).Free / 1GB"')
    if rc != 0:
        return False
    free_gb = float(out)
    print(f"  Espaço livre: {free_gb:.1f} GB")
    if free_gb < 35:
        print(f"  AVISO: Precisa de ~35GB. Só tem {free_gb:.1f}GB.")
        print("  Continuando sem chrome-profiles (vai usar modo cookies)...")
        return "sessions_only"
    return True


def step2_create_dirs(conn):
    """Cria estrutura de diretórios."""
    print("\n=== STEP 2: Criando diretórios ===")
    dirs = [
        "C:/projetos-navegador",
        "C:/projetos-navegador/engage_modules",
        "C:/projetos-navegador/shared",
        "C:/projetos-navegador/secrets",
        "C:/projetos-navegador/auto-refresh-sessoes",
        "C:/projetos-navegador/proxy_ext",
        "C:/logins-google",
        "C:/logins-google/sessions",
        "C:/logins-google/chrome-profiles",
    ]
    for d in dirs:
        conn.mkdir(d)
    print("  OK")


def step3_upload_code(conn):
    """Upload do código do projeto."""
    print("\n=== STEP 3: Upload do código (pode demorar ~2min) ===")

    src = Path("D:/projetos-navegador")

    # Upload arquivos raiz importantes
    essential = [
        "mega_engage.py",
        "engage_config.json",
        "all_channel_videos_full.json",
        "engage_server.py",
        "build_painel.py",
        "painel_template.html",
        "local_proxy.py",
        "RODAR_ENGAGE.bat",
        "_supervisor_engage.bat",
        "run_painel_server.bat",
    ]

    for f in essential:
        fp = src / f
        if fp.exists():
            conn.upload(str(fp), f"C:/projetos-navegador/{f}")

    # Upload pastas inteiras
    for folder in ["engage_modules", "shared", "auto-refresh-sessoes"]:
        fp = src / folder
        if fp.exists() and fp.is_dir():
            conn.upload(str(fp), "C:/projetos-navegador/")

    # proxy_ext se existir
    if (src / "proxy_ext").exists():
        conn.upload(str(src / "proxy_ext"), "C:/projetos-navegador/")

    print("  OK")


def step4_upload_sessions(conn, mode):
    """Upload de sessões/perfis Chrome."""
    if mode == "sessions_only":
        print("\n=== STEP 4: Upload de sessions (cookies — 1MB) ===")
        conn.upload("D:/logins-google/sessions", "C:/logins-google/")
    else:
        print("\n=== STEP 4: Upload de chrome-profiles (31GB — vai demorar 10-30min) ===")
        print("  Isso vai levar um tempo. Aguarde...")
        conn.upload("D:/logins-google/chrome-profiles", "C:/logins-google/")
        conn.upload("D:/logins-google/sessions", "C:/logins-google/")
    print("  OK")


def step5_upload_secrets(conn):
    """Upload de secrets (chaves Gemini)."""
    print("\n=== STEP 5: Upload de secrets ===")
    secrets_src = Path("D:/hipercool-videos/secrets/gemini_keys.json")
    if secrets_src.exists():
        conn.upload(str(secrets_src), "C:/projetos-navegador/secrets/gemini_keys.json")
    print("  OK")


def step6_patch_paths(conn):
    """Aplica patches de caminhos D: -> C:."""
    print("\n=== STEP 6: Patching caminhos D: -> C: ===")

    for rel in FILES_TO_PATCH:
        remote = f"C:/projetos-navegador/{rel}"

        # Lê arquivo remoto
        out, _, rc = conn.exec(f'powershell -c "Get-Content -Raw \'{remote}\' -ErrorAction SilentlyContinue"', print_output=False)
        if rc != 0 or not out:
            print(f"  SKIP {rel} (não encontrado)")
            continue

        content = out
        changed = False
        for old, new in PATH_MAP.items():
            if old in content:
                content = content.replace(old, new)
                changed = True

        if changed:
            # Salva localmente com patches
            tmp_local = Path(f"D:/projetos-navegador/_tmp_patch_{rel.replace('/', '_').replace('\\', '_')}")
            tmp_local.parent.mkdir(parents=True, exist_ok=True)
            tmp_local.write_text(content, encoding='utf-8')

            # Upload de volta
            conn.upload(str(tmp_local), remote)
            tmp_local.unlink()
            print(f"  PATCHED {rel}")
        else:
            print(f"  OK {rel} (sem mudanças)")

    print("  Todos os patches aplicados")


def step7_install_python(conn):
    """Instala Python + venv + dependências."""
    print("\n=== STEP 7: Setup Python + venv ===")

    # Verifica Python
    out, _, rc = conn.exec('powershell -c "(Get-Command python -ErrorAction SilentlyContinue).Path"')
    if rc != 0 or not out:
        print("  AVISO: Python não encontrado. Instale Python 3.11+ manualmente no PC3.")
        print("  Download: https://www.python.org/downloads/")
        return False

    python_path = out
    print(f"  Python encontrado: {python_path}")

    # Cria venv
    print("  Criando venv...")
    conn.exec(f'"{python_path}" -m venv C:/projetos-navegador/venv')

    # Instala dependências
    print("  Instalando dependências (pode levar 2-5min)...")
    conn.exec('"C:/projetos-navegador/venv/Scripts/pip.exe" install --quiet playwright scp paramiko')
    conn.exec('"C:/projetos-navegador/venv/Scripts/python.exe" -m playwright install chromium')

    print("  OK")
    return True


def step8_test(conn):
    """Teste básico: importa o módulo."""
    print("\n=== STEP 8: Teste de importação ===")
    test_cmd = (
        '"C:/projetos-navegador/venv/Scripts/python.exe" -c '
        '"import sys; sys.path.insert(0, \'C:/projetos-navegador\'); '
        'from engage_modules.config import BASE_DIR, load_config; '
        'print(f\'BASE_DIR={BASE_DIR}\'); '
        'cfg=load_config(); print(f\'workers={cfg[\\\"workers\\\"]}\'); '
        'print(\'IMPORT_OK\')"'
    )
    out, err, rc = conn.exec(test_cmd)

    if "IMPORT_OK" in out:
        print("  SUCESSO! Projeto funcional no PC3.")
        return True
    else:
        print(f"  FALHA na importação:")
        print(f"    {err}")
        return False


def main():
    print("=" * 70)
    print("DEPLOY: projetos-navegador -> PC3")
    print(f"Target: {PC3_USER}@{PC3_IP}")
    print("=" * 70)

    with PC3Connection() as conn:
        disk = step1_check_disk(conn)
        if disk is False:
            print("\nABORTADO: sem espaço suficiente.")
            return

        step2_create_dirs(conn)
        step3_upload_code(conn)
        step4_upload_sessions(conn, disk if isinstance(disk, str) else "full")
        step5_upload_secrets(conn)
        step6_patch_paths(conn)

        if not step7_install_python(conn):
            print("\nAVISO: Python não instalado. Instale manualmente e rode:")
            print('  python -m venv C:\\projetos-navegador\\venv')
            print('  C:\\projetos-navegador\\venv\\Scripts\\pip install playwright scp paramiko')
            print('  C:\\projetos-navegador\\venv\\Scripts\\python -m playwright install chromium')
        else:
            step8_test(conn)

    print("\n" + "=" * 70)
    print("DEPLOY COMPLETO")
    print("\nPara rodar no PC3 (cole no outro chat):")
    print("  cd C:\\projetos-navegador")
    print("  C:\\projetos-navegador\\venv\\Scripts\\python.exe mega_engage.py")
    print("\nOu pelo batch:")
    print("  C:\\projetos-navegador\\RODAR_ENGAGE.bat")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrompido pelo usuário.")
    except Exception as e:
        print(f"\n\nERRO FATAL: {e}")
        import traceback
        traceback.print_exc()
