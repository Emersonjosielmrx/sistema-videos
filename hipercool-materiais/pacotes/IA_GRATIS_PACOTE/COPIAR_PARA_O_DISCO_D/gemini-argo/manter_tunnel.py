#!/usr/bin/env python3
r"""Mantém o SSH reverse tunnel para o proxy Argon.

Roda como tarefa agendada ou fica em loop.
VPS hermes-bloqueio:20141 -> PC local:20141 (gemini_http_proxy.py, sem navegador)
"""
import subprocess
import time
import sys
import socket

PORTA = 20141
VPS = "hermes-bloqueio"


def tunnel_ativo():
    try:
        r = subprocess.run(
            ["ssh", VPS, f"ss -tlnp | grep :{PORTA}"],
            capture_output=True, text=True, timeout=10,
        )
        return str(PORTA) in r.stdout
    except Exception:
        return False


def proxy_local_ativo():
    try:
        s = socket.create_connection(("127.0.0.1", PORTA), timeout=3)
        s.close()
        return True
    except Exception:
        return False


def criar_tunnel():
    subprocess.Popen(
        ["ssh", "-f", "-N", "-o", "ServerAliveInterval=30",
         "-o", "ServerAliveCountMax=3", "-o", "ExitOnForwardFailure=yes",
         "-R", f"{PORTA}:localhost:{PORTA}", VPS],
        creationflags=0x00000008,  # DETACHED_PROCESS
    )


def main():
    loop = "--loop" in sys.argv
    while True:
        if not proxy_local_ativo():
            print(f"Proxy local na {PORTA} nao responde")
        elif not tunnel_ativo():
            print(f"Tunnel caiu, recriando...")
            criar_tunnel()
            time.sleep(3)
            if tunnel_ativo():
                print("Tunnel restaurado")
            else:
                print("Falha ao restaurar tunnel")
        else:
            print("Tunnel ok")
        if not loop:
            break
        time.sleep(60)


if __name__ == "__main__":
    main()
