"""
Objetivo 51: Bandwidth Sharing via Google Colab.
Conecta em proxies de bandwidth sharing (Honeygain, PacketStream, etc)
usando sessões Colab das contas Google.
"""
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from google_session import ACCOUNTS, google_browser, save_session

BW_DIR = Path(__file__).resolve().parent
STATUS_FILE = BW_DIR / "bandwidth_status.json"
CONFIG_FILE = BW_DIR / "config.json"
COLAB_URL = "https://colab.research.google.com/"


def carregar_config():
    """Lê credenciais reais de config.json (gitignored). Vazio = placeholders."""
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    modelo = {
        "honeygain": {"email": "", "password": ""},
        "packetstream": {"cid": ""},
        "earnapp": {"node_id": ""},
    }
    CONFIG_FILE.write_text(json.dumps(modelo, indent=2), encoding="utf-8")
    return modelo

NOTEBOOK_CODE = '''
# Bandwidth Sharing Node
# Roda em background no Colab, compartilha bandwidth ociosa

import subprocess
import os
import time

def setup_honeygain(email, password):
    """Instala e configura Honeygain CLI."""
    cmds = [
        "wget -q https://github.com/nicehash/honeygain-cli/releases/latest/download/honeygain-linux-amd64 -O /tmp/honeygain",
        "chmod +x /tmp/honeygain",
    ]
    for cmd in cmds:
        os.system(cmd)

    os.system(f"/tmp/honeygain -tac-accept -email {email} -pass {password} &")
    print("Honeygain iniciado!")

def setup_packetstream(cid):
    """Configura PacketStream residential proxy."""
    cmds = [
        "apt-get update -qq && apt-get install -y -qq curl > /dev/null",
        f"curl -s https://packetstream.io/install.sh | CID={cid} bash",
    ]
    for cmd in cmds:
        os.system(cmd)
    print("PacketStream iniciado!")

def setup_earnapp(node_id):
    """Configura EarnApp bandwidth sharing."""
    cmds = [
        "wget -qO- https://brightdata.com/static/earnapp/install.sh | sudo bash -s -- {node_id}",
    ]
    for cmd in cmds:
        os.system(cmd)
    print("EarnApp iniciado!")

def keep_alive():
    """Mantém o Colab runtime ativo."""
    while True:
        print(f"[{time.strftime('%H:%M:%S')}] Runtime ativo, bandwidth sharing rodando...")
        time.sleep(300)

# Descomentar e configurar:
# setup_honeygain("email@gmail.com", "senha")
# setup_packetstream("SEU_CID")
# setup_earnapp("SEU_NODE_ID")
# keep_alive()
'''


def create_colab_notebook(account, output_path, config=None):
    """Gera um .ipynb para bandwidth sharing, injetando credenciais do config."""
    config = config or {}
    hg = config.get("honeygain", {})
    ps = config.get("packetstream", {})
    ea = config.get("earnapp", {})

    ativacao = []
    if hg.get("email") and hg.get("password"):
        ativacao.append(f'setup_honeygain("{hg["email"]}", "{hg["password"]}")')
    if ps.get("cid"):
        ativacao.append(f'setup_packetstream("{ps["cid"]}")')
    if ea.get("node_id"):
        ativacao.append(f'setup_earnapp("{ea["node_id"]}")')
    ativacao.append("keep_alive()")
    bloco_ativacao = "\n".join(ativacao)

    notebook = {
        "nbformat": 4,
        "nbformat_minor": 0,
        "metadata": {
            "colab": {
                "provenance": [],
                "name": f"BandwidthShare_{account}",
            },
            "kernelspec": {
                "name": "python3",
                "display_name": "Python 3",
            },
        },
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# Bandwidth Sharing Node\n",
                    f"Conta: {account}\n",
                    "Roda Honeygain/PacketStream/EarnApp em background.\n",
                    "**Não feche esta aba** — o runtime precisa ficar ativo.",
                ],
            },
            {
                "cell_type": "code",
                "metadata": {},
                "source": NOTEBOOK_CODE.split("\n"),
                "execution_count": None,
                "outputs": [],
            },
            {
                "cell_type": "code",
                "metadata": {},
                "source": [
                    "# Ativação (preenchida a partir de config.json)\n",
                    bloco_ativacao if bloco_ativacao.strip() != "keep_alive()" else "# configure config.json pra ativar provedores\nkeep_alive()",
                ],
                "execution_count": None,
                "outputs": [],
            },
            {
                "cell_type": "code",
                "metadata": {},
                "source": [
                    "# Keep-alive: imprime heartbeat a cada 5 min\n",
                    "import time\n",
                    "while True:\n",
                    "    print(f'Heartbeat: {time.strftime(\"%H:%M:%S\")} — runtime ativo')\n",
                    "    time.sleep(300)\n",
                ],
                "execution_count": None,
                "outputs": [],
            },
        ],
    }

    output_path.write_text(json.dumps(notebook, indent=2, ensure_ascii=False), encoding="utf-8")
    return output_path


def upload_notebook_to_colab(account, notebook_path):
    """Faz upload de notebook ao Colab via interface."""
    try:
        with google_browser(account) as (page, context, browser):
            page.goto(COLAB_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)

            if "accounts.google.com" in page.url:
                return {"success": False, "error": "session_expired"}

            upload_btn = page.query_selector('button:has-text("Upload"), button:has-text("Fazer upload")')
            if upload_btn:
                upload_btn.click()
                time.sleep(2)

                file_input = page.query_selector('input[type="file"]')
                if file_input:
                    file_input.set_input_files(str(notebook_path))
                    time.sleep(5)
                    save_session(context, account)
                    return {"success": True, "account": account}

            return {"success": False, "error": "upload interface not found"}

    except Exception as e:
        return {"success": False, "error": str(e)}


def setup_bandwidth_sharing(dry_run=True):
    """Configura bandwidth sharing em todas as contas."""
    print(f"[Bandwidth Sharing] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    notebooks_dir = BW_DIR / "notebooks"
    notebooks_dir.mkdir(exist_ok=True)

    status = {"accounts": {}, "last_run": datetime.now(timezone.utc).isoformat()}
    config = carregar_config()
    provedores_ativos = [k for k, v in config.items() if any(v.values())]
    print(f"  Provedores configurados: {provedores_ativos or 'nenhum (edite config.json)'}")

    for account in ACCOUNTS:
        nb_path = notebooks_dir / f"bandwidth_{account}.ipynb"
        create_colab_notebook(account, nb_path, config)
        print(f"  Notebook criado: {nb_path.name}")

        if dry_run:
            status["accounts"][account] = {
                "notebook": str(nb_path),
                "uploaded": False,
                "dry_run": True,
            }
        else:
            result = upload_notebook_to_colab(account, nb_path)
            status["accounts"][account] = {
                "notebook": str(nb_path),
                "uploaded": result.get("success", False),
                "error": result.get("error"),
            }

    STATUS_FILE.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nNotebooks gerados em {notebooks_dir}")
    print(f"Status salvo em {STATUS_FILE}")

    if dry_run:
        print("\n[DRY RUN] Use --live pra fazer upload pro Colab")

    return status


if __name__ == "__main__":
    dry = "--live" not in sys.argv
    setup_bandwidth_sharing(dry_run=dry)
