#!/usr/bin/env python3
# Helper SSH read-only pra VPS de teste do bloqueio. Uso: python _ssh.py "comando"
import sys, paramiko

HOST = "157.173.207.22"
USER = "root"
PWD  = "<SEGREDO_REMOVIDO>"

def run(cmd, timeout=60):
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username=USER, password=PWD, timeout=20, look_for_keys=False, allow_agent=False)
    _, out, err = c.exec_command(cmd, timeout=timeout)
    o = out.read().decode(errors="replace")
    e = err.read().decode(errors="replace")
    c.close()
    return o, e

def _exec(c, cmd, stdin_data=None, timeout=120):
    chan = c.get_transport().open_session()
    chan.settimeout(timeout)
    chan.exec_command(cmd)
    if stdin_data is not None:
        chan.sendall(stdin_data)
        chan.shutdown_write()
    out = b""
    err = b""
    while True:
        if chan.recv_ready():
            out += chan.recv(65536)
        if chan.recv_stderr_ready():
            err += chan.recv_stderr(65536)
        if chan.exit_status_ready() and not chan.recv_ready() and not chan.recv_stderr_ready():
            break
    rc = chan.recv_exit_status()
    msg = out.decode(errors="replace")
    if err.strip():
        msg += "\n[stderr] " + err.decode(errors="replace")
    return rc, msg

def put(local, remote):
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username=USER, password=PWD, timeout=30, look_for_keys=False, allow_agent=False)
    sftp = c.open_sftp()
    sftp.put(local, remote)
    sftp.close()
    rc, o = _exec(c, f"chmod +x {remote} && sha256sum {remote} | cut -d' ' -f1")
    c.close()
    print(f"uploaded -> {remote} (rc={rc}) sha256={o.strip()}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "put":
        put(sys.argv[2], sys.argv[3])
    else:
        cmd = sys.argv[1] if len(sys.argv) > 1 else "echo ok"
        o, e = run(cmd)
        sys.stdout.write(o)
        if e.strip():
            sys.stderr.write("\n[stderr]\n" + e)
