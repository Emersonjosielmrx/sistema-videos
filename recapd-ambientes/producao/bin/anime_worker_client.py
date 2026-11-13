#!/usr/bin/env python3
"""anime_worker_client.py — despacha tarefas pro worker anime no PC2.

Usa o daemon anime_worker_daemon.py (porta 8772, Tailscale 100.125.7.77).

API:
    health(host, port) -> dict ou None
    is_online(host, port) -> bool
    run_anime(host, port, payload, timeout_s) -> dict ou None
"""
import json
import urllib.error
import urllib.request
import urllib.parse


def health(host, port, timeout=10.0):
    url = f"http://{host}:{port}/health"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            if r.status == 200:
                return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None
    return None


def is_online(host, port, timeout=10.0):
    return health(host, port, timeout) is not None


def run_anime(host, port, payload, timeout=4000):
    """POST /run-anime. Retorna dict de resultado ou None em qualquer falha."""
    url = f"http://{host}:{port}/run-anime"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    import logging
    import time
    # 3 tentativas: 17/10 09:44 a 1ª chamada falhou na hora ("sem resposta") com o worker no ar, e o anime longo
    # perdeu 1 h de roteiro. O erro agora vai pro log em vez de sumir.
    for tent in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[worker] /run-anime falhou ({tent + 1}/3): {type(e).__name__}: {str(e)[:200]}")
            if tent < 2:
                time.sleep(60)
    return None


def baixar(host, port, remote_path, destino, timeout=600):
    """GET /download/<b64>. Baixa um arquivo do PC2 pro PC1 (streaming).
    Retorna True se baixou e o arquivo tem tamanho > 0."""
    import base64
    import os
    b64 = base64.urlsafe_b64encode(str(remote_path).encode()).decode()
    url = f"http://{host}:{port}/download/{b64}"
    destino = str(destino)
    try:
        os.makedirs(os.path.dirname(destino) or ".", exist_ok=True)
        with urllib.request.urlopen(url, timeout=timeout) as r:
            if getattr(r, "status", 200) != 200:
                return False
            with open(destino, "wb") as f:
                while True:
                    chunk = r.read(1024 * 256)
                    if not chunk:
                        break
                    f.write(chunk)
        return os.path.exists(destino) and os.path.getsize(destino) > 0
    except Exception:
        return False


def limpar(host, port, work_dir, timeout=60):
    """POST /cleanup. Apaga o work_dir do PC2 (chamar SO depois de baixar OK).
    Retorna o dict de resposta ou None."""
    url = f"http://{host}:{port}/cleanup"
    data = json.dumps({"work_dir": str(work_dir)}).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def disco(host, port, timeout=6):
    """GET /disk. Espaco livre no PC2. Retorna dict ou None."""
    url = f"http://{host}:{port}/disk"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None
