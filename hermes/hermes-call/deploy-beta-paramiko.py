#!/usr/bin/env python3
"""Deploy Hermes Call via paramiko (SSH + SFTP with password)."""
import os
import sys
import tarfile
import time
import getpass
import paramiko

VPS = "62.171.128.241"
USER = "root"
PASSWORD = os.environ.get("VPS_PASS") or sys.argv[1] if len(sys.argv) > 1 else None
REMOTE_DIR = "/opt/hermes-call"
SERVICE = "hermescall"
LOCAL_ROOT = r"D:\hipercool-refactor"
TAR = "hermescall-deploy.tar.gz"


def run_local(cmd):
    print(f"$ {cmd}")
    return os.system(cmd)


def main():
    password = os.environ.get("VPS_PASS")
    if not password and len(sys.argv) > 1:
        password = sys.argv[1]
    if not password:
        password = getpass.getpass("VPS password: ")
    PASSWORD = password

    # 1) build (idempotente: assume já compilado em ./bin e ./client/dist)
    print("\n--- deploying to VPS via paramiko ---")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(VPS, username=USER, password=PASSWORD, timeout=30, look_for_keys=False, allow_agent=False)
    sftp = client.open_sftp()

    # 2) sobe o tar.gz
    print(f"--- uploading {TAR} ---")
    sftp.put(os.path.join(LOCAL_ROOT, TAR), f"{REMOTE_DIR}/{TAR}")

    # 3) extrai e reinicia
    print("--- extracting + restarting ---")
    cmds = [
        f"cd {REMOTE_DIR} && tar -xzf {TAR} && rm {TAR}",
        f"systemctl restart {SERVICE}",
        "sleep 3",
        f"systemctl is-active {SERVICE}",
        f"curl -s -o /dev/null -w 'HTTP %{http_code}\\n' http://127.0.0.1:8080/healthz",
        f"journalctl -u {SERVICE} --no-pager -n 15 | tail -20",
    ]
    for c in cmds:
        print(f"$ {c}")
        si, so, se = client.exec_command(c)
        out = so.read().decode("utf-8", errors="replace")
        err = se.read().decode("utf-8", errors="replace")
        if out: print(out)
        if err: print("STDERR:", err)

    sftp.close()
    client.close()
    print("\n=== DEPLOY OK ===")


if __name__ == "__main__":
    main()