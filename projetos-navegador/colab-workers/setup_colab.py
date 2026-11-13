"""
Objetivo 8: Colab Workers — roda workers em Colabs e cria proxy pool.
"""
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from google_session import ACCOUNTS, google_browser, save_session

COLAB_DIR = Path(__file__).resolve().parent
STATUS_FILE = COLAB_DIR / "colab_status.json"
COLAB_URL = "https://colab.research.google.com/"


def upload_notebook_to_colab(account, notebook_path):
    """Faz upload de notebook worker ao Colab."""
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

WORKER_NOTEBOOK_CODE = '''
# Worker Colab: proxy + tarefas background

import subprocess
import os
import time
import threading

def install_deps():
    """Instala dependências básicas."""
    os.system("pip install -q flask requests pyngrok")

def run_proxy(port=5000):
    """Roda um proxy HTTP simples."""
    from flask import Flask, request, Response
    import requests as req

    app = Flask(__name__)

    @app.route('/proxy', methods=['GET', 'POST'])
    def proxy():
        url = request.args.get('url')
        if not url:
            return Response("Falta ?url=", status=400)
        try:
            r = req.get(url, timeout=30)
            return Response(r.content, status=r.status_code,
                          headers={'Content-Type': r.headers.get('Content-Type', 'text/html')})
        except Exception as e:
            return Response(str(e), status=500)

    @app.route('/health')
    def health():
        return {"status": "ok", "uptime": time.time()}

    app.run(host='0.0.0.0', port=port)

def expose_ngrok(port=5000):
    """Expõe o proxy via ngrok."""
    from pyngrok import ngrok
    tunnel = ngrok.connect(port)
    print(f"Proxy público: {tunnel.public_url}")
    return tunnel.public_url

def run_worker():
    """Inicia worker completo."""
    install_deps()
    t = threading.Thread(target=run_proxy, daemon=True)
    t.start()
    time.sleep(2)
    url = expose_ngrok()
    print(f"Worker ativo! URL: {url}")

    while True:
        print(f"[{time.strftime('%H:%M:%S')}] Worker rodando, proxy em {url}")
        time.sleep(300)

# run_worker()
'''


def create_worker_notebook(account, output_path):
    """Cria notebook de worker."""
    notebook = {
        "nbformat": 4,
        "nbformat_minor": 0,
        "metadata": {
            "colab": {"provenance": [], "name": f"Worker_{account}"},
            "kernelspec": {"name": "python3", "display_name": "Python 3"},
        },
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [f"# Worker Node — {account}\n", "Proxy + tarefas background no Colab.\n"],
            },
            {
                "cell_type": "code",
                "metadata": {},
                "source": ["!pip install -q flask requests pyngrok\n"],
                "execution_count": None,
                "outputs": [],
            },
            {
                "cell_type": "code",
                "metadata": {},
                "source": WORKER_NOTEBOOK_CODE.split("\n"),
                "execution_count": None,
                "outputs": [],
            },
        ],
    }

    output_path.write_text(json.dumps(notebook, indent=2, ensure_ascii=False), encoding="utf-8")
    return output_path


def setup_colab_workers(dry_run=True):
    """Setup workers Colab."""
    print(f"[Colab Workers] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    notebooks_dir = COLAB_DIR / "notebooks"
    notebooks_dir.mkdir(exist_ok=True)

    status = {"accounts": {}, "last_run": datetime.now(timezone.utc).isoformat()}

    for account in ACCOUNTS:
        nb_path = notebooks_dir / f"worker_{account}.ipynb"
        create_worker_notebook(account, nb_path)
        print(f"  Notebook criado: {nb_path.name}")
        entry = {"notebook": str(nb_path), "uploaded": False, "dry_run": dry_run}
        if not dry_run:
            r = upload_notebook_to_colab(account, nb_path)
            entry["uploaded"] = r.get("sucesso", False)
            entry["erro"] = r.get("erro")
        status["accounts"][account] = entry

    STATUS_FILE.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nNotebooks em {notebooks_dir}")
    print(f"Status: {STATUS_FILE}")
    return status


if __name__ == "__main__":
    dry = "--live" not in sys.argv
    setup_colab_workers(dry_run=dry)
