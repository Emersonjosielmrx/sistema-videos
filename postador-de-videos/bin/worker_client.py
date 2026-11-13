#!/usr/bin/env python3
"""worker_client.py — transporte HTTP pro worker remoto (render distribuído).

REGRA DE OURO (aprendida na marra): health-check é por HTTP/TCP, NUNCA por ping.
O firewall do Windows bloqueia ICMP entre as máquinas — ping dá timeout mesmo com
a porta TCP aberta e funcionando. Sempre teste com /health, não com ping.

Contrato com o daemon do worker (PC2):
    GET  /health        -> 200 {"ok": true, "cores": N, "ffmpeg": bool}
    POST /run-chapter    -> 200 {"ok": bool, "outputs": [<paths relativos>], "log": str}
        body: {"cap": int, "obra": str, "dual": bool,
               "gemini_key_range": [lo, hi]|null, "timeout_s": int}
"""
import json
import urllib.error
import urllib.request


def health(host, port, timeout=2.0):
    """Retorna o dict do /health, ou None se offline/erro. Timeout curto de propósito."""
    url = f"http://{host}:{port}/health"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            if r.status == 200:
                return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None
    return None


def is_online(host, port, timeout=2.0):
    return health(host, port, timeout) is not None


def run_chapter(host, port, payload, timeout):
    """POST /run-chapter. Retorna o dict de resultado, ou None em qualquer falha
    (o caller deve cair pro fallback local). Timeout longo (render demora)."""
    url = f"http://{host}:{port}/run-chapter"
    data = json.dumps(payload).encode("utf-8")
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
