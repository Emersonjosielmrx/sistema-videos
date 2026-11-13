#!/usr/bin/env python3
"""Deploy Hermes Call via wexpect (PTY SSH com senha)."""
import os
import sys
import time
import wexpect as pexpect

VPS = "62.171.128.241"
USER = "root"
REMOTE_DIR = "/opt/hermes-call"
SERVICE = "hermescall"
TAR = "hermescall-deploy.tar.gz"


def ssh_cmd(shell, cmd, timeout=60):
    shell.sendline(cmd)
    shell.expect([r"\$", r"#", pexpect.TIMEOUT], timeout=timeout)
    output = shell.before or ""
    return output


def main():
    password = os.environ.get("VPS_PASS")
    if not password and len(sys.argv) > 1:
        password = sys.argv[1]
    if not password:
        password = input("VPS password: ")
    PASSWORD = password

    # 1) SCP — vamos usar o scp do sistema via spawn (mais simples que pexpect ssh).
    print("\n--- SCP upload ---")
    scp_cmd = f'scp -o StrictHostKeyChecking=no -o ConnectTimeout=30 {TAR} {USER}@{VPS}:{REMOTE_DIR}/'
    child = pexpect.spawn(scp_cmd, timeout=180, encoding='utf-8')
    idx = child.expect(['password:', pexpect.EOF, pexpect.TIMEOUT])
    if idx != 0:
        print("SCP não pediu senha — provavel erro de conexão.")
        print(child.before)
        sys.exit(1)
    child.sendline(PASSWORD)
    child.expect(pexpect.EOF, timeout=180)
    print(child.before or "")
    if child.exitstatus != 0:
        print(f"SCP falhou: exit={child.exitstatus}")
        sys.exit(1)

    # 2) SSH — extrai e reinicia
    print("\n--- SSH restart ---")
    ssh = pexpect.spawn(f'ssh -o StrictHostKeyChecking=no -o ConnectTimeout=30 {USER}@{VPS}',
                       timeout=60, encoding='utf-8')
    idx = ssh.expect(['password:', r'\$', r'#', pexpect.TIMEOUT])
    if idx == 0:
        ssh.sendline(PASSWORD)
        ssh.expect([r'\$', r'#', pexpect.TIMEOUT], timeout=30)
    elif idx in (1, 2):
        pass  # já dentro
    else:
        print("SSH não conectou"); print(ssh.before); sys.exit(1)

    for cmd in [
        f"cd {REMOTE_DIR} && tar -xzf {TAR} && rm {TAR}",
        f"systemctl restart {SERVICE}",
        "sleep 3",
        f"systemctl is-active {SERVICE}",
        f"curl -s -o /dev/null -w 'HTTP %{{http_code}}\\n' http://127.0.0.1:8080/healthz",
        f"journalctl -u {SERVICE} --no-pager -n 15",
        "exit",
    ]:
        print(f"\n$ {cmd}")
        ssh.sendline(cmd)
        ssh.expect([r'\$', r'#', pexpect.TIMEOUT, 'password:'], timeout=30)
        out = ssh.before or ""
        print(out)
    ssh.close()
    print("\n=== DEPLOY OK ===")


if __name__ == "__main__":
    main()