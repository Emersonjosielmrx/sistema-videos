r"""
Deploy projetos-navegador para PC3 (100.108.160.85) via SSH/SFTP.

Pré-requisito: o PC3 precisa ter a chave SSH autorizada.
Cole no chat do PC3:

    $pubkey = "COLE_A_CHAVE_PUBLICA_AQUI"
    $authFile = "C:\Users\Emerson-IA\.ssh\authorized_keys"
    New-Item -ItemType Directory -Force -Path "C:\Users\Emerson-IA\.ssh"
    if (-not (Test-Path $authFile) -or -not (Select-String -Path $authFile -Pattern $pubkey -Quiet)) {
        Add-Content -Path $authFile -Value $pubkey
    }

Depois rode este script daqui do PC1:
    python D:/projetos-navegador/_deploy_pc3.py
"""

import subprocess
import sys
import os
import json
import time
from pathlib import Path

PC3_IP = "100.108.160.85"
PC3_USER = "Emerson-IA"
SSH_KEY = r"C:\Users\Haylla\.ssh\id_rsa_pc2"
SSH_OPTS = ["-i", SSH_KEY, "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10"]

# Mapeamento de caminhos D: (PC1) → C: (PC3)
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


def ssh(cmd, check=True):
    """Roda comando no PC3 via SSH."""
    full = ["ssh"] + SSH_OPTS + [f"{PC3_USER}@{PC3_IP}", cmd]
    print(f"  SSH> {cmd}")
    r = subprocess.run(full, capture_output=True, text=True, timeout=30)
    if r.returncode != 0 and check:
        print(f"  ERRO: {r.stderr.strip()}")
    return r


def scp_upload(local, remote):
    """Upload via SCP."""
    full = ["scp", "-r"] + SSH_OPTS + [local, f"{PC3_USER}@{PC3_IP}:{remote}"]
    print(f"  SCP> {local} → {remote}")
    r = subprocess.run(full, capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        print(f"  ERRO SCP: {r.stderr.strip()}")
    return r


def step1_test_ssh():
    """Testa conexão SSH."""
    print("\n=== STEP 1: Testando SSH ===")
    r = ssh("hostname", check=False)
    if r.returncode != 0:
        print("FALHA: SSH não conectou. Verifique se a chave está autorizada no PC3.")
        print("Cole no PowerShell do PC3:")
        pubkey_path = SSH_KEY + ".pub"
        pubkey = Path(pubkey_path).read_text().strip()
        print(f"""
    $authFile = "C:\\Users\\Emerson-IA\\.ssh\\authorized_keys"
    New-Item -ItemType Directory -Force -Path "C:\\Users\\Emerson-IA\\.ssh"
    Add-Content -Path $authFile -Value '{pubkey}'
        """)
        return False
    print(f"  OK — hostname: {r.stdout.strip()}")
    return True


def step2_check_disk():
    """Verifica espaço em disco no PC3."""
    print("\n=== STEP 2: Verificando disco no PC3 ===")
    r = ssh('powershell -c "(Get-PSDrive C).Free / 1GB"')
    if r.returncode != 0:
        return False
    free_gb = float(r.stdout.strip())
    print(f"  Espaço livre: {free_gb:.1f} GB")
    if free_gb < 35:
        print(f"  AVISO: Precisa de ~35GB (31GB profiles + 4GB venv). Só tem {free_gb:.1f}GB.")
        print("  Continuando sem chrome-profiles (vai usar modo cookies)...")
        return "sessions_only"
    return True


def step3_create_dirs():
    """Cria estrutura de diretórios no PC3."""
    print("\n=== STEP 3: Criando diretórios ===")
    dirs = [
        "C:/projetos-navegador",
        "C:/projetos-navegador/engage_modules",
        "C:/projetos-navegador/shared",
        "C:/projetos-navegador/secrets",
        "C:/logins-google/sessions",
        "C:/logins-google/chrome-profiles",
        "C:/projetos-navegador/auto-refresh-sessoes",
    ]
    for d in dirs:
        ssh(f'powershell -c "New-Item -ItemType Directory -Force -Path \'{d}\'"', check=False)
    print("  OK")


def step4_upload_project():
    """Faz upload do código do projeto."""
    print("\n=== STEP 4: Upload do código ===")

    # Arquivos e pastas essenciais
    essential = [
        "mega_engage.py",
        "engage_config.json",
        "all_channel_videos_full.json",
        "engage_server.py",
        "build_painel.py",
        "painel_template.html",
        "create_template.py",
        "discover_channels.py",
        "scan_new_channels.py",
        "orchestrator.py",
        "add_new_accounts.py",
        "youtube_engage.py",
        "youtube_engage_batch2.py",
        "youtube_engage_retry.py",
        "local_proxy.py",
        "dead_accounts.txt",
        "RODAR_ENGAGE.bat",
        "_supervisor_engage.bat",
        "run_painel_server.bat",
    ]

    src = Path("D:/projetos-navegador")

    # Upload arquivos raiz
    for f in essential:
        fp = src / f
        if fp.exists():
            scp_upload(str(fp), f"C:/projetos-navegador/{f}")

    # Upload pastas
    for folder in ["engage_modules", "shared", "auto-refresh-sessoes", "proxy_ext"]:
        fp = src / folder
        if fp.exists():
            scp_upload(str(fp), "C:/projetos-navegador/")

    print("  OK")


def step5_upload_sessions(mode):
    """Upload de sessões/perfis Chrome."""
    if mode == "sessions_only":
        print("\n=== STEP 5: Upload de sessions (cookies) ===")
        scp_upload("D:/logins-google/sessions/", "C:/logins-google/sessions/")
    else:
        print("\n=== STEP 5: Upload de chrome-profiles (31GB — vai demorar) ===")
        scp_upload("D:/logins-google/chrome-profiles/", "C:/logins-google/")
        scp_upload("D:/logins-google/sessions/", "C:/logins-google/sessions/")
    print("  OK")


def step6_upload_secrets():
    """Upload de secrets (chaves Gemini pra smart_comments)."""
    print("\n=== STEP 6: Upload de secrets ===")
    secrets_src = Path("D:/hipercool-videos/secrets/gemini_keys.json")
    if secrets_src.exists():
        scp_upload(str(secrets_src), "C:/projetos-navegador/secrets/gemini_keys.json")
    print("  OK")


def step7_patch_paths():
    """Aplica patches de caminhos D: → C: remotamente."""
    print("\n=== STEP 7: Patching caminhos D: → C: ===")

    for rel in FILES_TO_PATCH:
        remote = f"C:/projetos-navegador/{rel}"
        print(f"  Patching {rel}...")

        # Lê o arquivo remoto
        r = ssh(f'powershell -c "Get-Content -Raw \'{remote}\' -ErrorAction SilentlyContinue"', check=False)
        if r.returncode != 0 or not r.stdout.strip():
            print(f"    SKIP (não encontrado)")
            continue

        content = r.stdout
        changed = False
        for old, new in PATH_MAP.items():
            if old in content:
                content = content.replace(old, new)
                changed = True

        if changed:
            # Escreve de volta (escapa aspas simples pro PowerShell)
            escaped = content.replace("'", "''")
            # Usa arquivo temporário pra evitar problemas de encoding
            tmp_local = Path(f"D:/projetos-navegador/_tmp_patch_{rel.replace('/', '_')}")
            tmp_local.write_text(content, encoding="utf-8")
            scp_upload(str(tmp_local), remote)
            tmp_local.unlink()
            print(f"    PATCHED")
        else:
            print(f"    (sem mudança)")

    print("  OK")


def step8_setup_venv():
    """Cria venv e instala dependências no PC3."""
    print("\n=== STEP 8: Setup Python + venv ===")

    # Verifica se Python existe
    r = ssh('powershell -c "(Get-Command python -ErrorAction SilentlyContinue).Path"', check=False)
    if r.returncode != 0 or not r.stdout.strip():
        print("  AVISO: Python não encontrado no PC3. Instale Python 3.13 manualmente.")
        return False

    python_path = r.stdout.strip()
    print(f"  Python encontrado: {python_path}")

    # Cria venv
    ssh(f'"{python_path}" -m venv C:/projetos-navegador/venv', check=False)

    # Instala dependências
    deps = "playwright selenium requests"
    ssh(f'"C:/projetos-navegador/venv/Scripts/pip.exe" install {deps}')
    ssh('"C:/projetos-navegador/venv/Scripts/python.exe" -m playwright install chromium')

    print("  OK")


def step9_test():
    """Teste básico: importa o módulo e verifica."""
    print("\n=== STEP 9: Teste de importação ===")
    test_cmd = (
        '"C:/projetos-navegador/venv/Scripts/python.exe" -c '
        '"import sys; sys.path.insert(0, \'C:/projetos-navegador\'); '
        'from engage_modules.config import BASE_DIR, load_config; '
        'print(f\'BASE_DIR={BASE_DIR}\'); '
        'cfg=load_config(); print(f\'workers={cfg.get(\\\"workers\\\")}\'); '
        'print(\'IMPORT OK\')"'
    )
    r = ssh(test_cmd, check=False)
    print(f"  {r.stdout.strip()}")
    if "IMPORT OK" in r.stdout:
        print("  SUCESSO!")
        return True
    else:
        print(f"  FALHA: {r.stderr.strip()}")
        return False


def main():
    print("=" * 60)
    print("DEPLOY: projetos-navegador → PC3")
    print(f"Target: {PC3_USER}@{PC3_IP}")
    print("=" * 60)

    if not step1_test_ssh():
        return

    disk = step2_check_disk()
    if disk is False:
        return

    step3_create_dirs()
    step4_upload_project()
    step5_upload_sessions(disk if isinstance(disk, str) else "full")
    step6_upload_secrets()
    step7_patch_paths()
    step8_setup_venv()
    step9_test()

    print("\n" + "=" * 60)
    print("DEPLOY COMPLETO")
    print("Para rodar no PC3:")
    print('  ssh Emerson-IA@100.108.160.85')
    print('  cd C:\\projetos-navegador')
    print('  C:\\projetos-navegador\\venv\\Scripts\\python.exe mega_engage.py')
    print("=" * 60)


if __name__ == "__main__":
    main()
